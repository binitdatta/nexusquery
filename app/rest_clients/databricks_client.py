"""
DuckDB Delta Client
Reads Gold Delta tables directly from ADLS Gen2 using DuckDB.

No Databricks cluster is required for chat queries.
"""
from __future__ import annotations

import logging
from typing import Any

import duckdb
from flask import current_app

logger = logging.getLogger(__name__)

GOLD_TABLES = [
    "fact_spend_by_supplier",
    "fact_spend_by_category",
    "fact_otd_by_supplier",
    "fact_invoice_match",
    "fact_budget_variance",
    "fact_defect_rate",
]


class DatabricksClient:
    """
    Reads Gold Delta tables from ADLS Gen2 via DuckDB.

    This class keeps the existing DatabricksClient name/interface used by the
    application, but internally reads Delta files directly from ADLS Gen2.
    """

    def __init__(self) -> None:
        self._account = current_app.config["AZURE_STORAGE_ACCOUNT_NAME"]
        self._key = current_app.config["AZURE_STORAGE_ACCOUNT_KEY"]
        self._gold_base = current_app.config["ADLS_GOLD_BASE"]
        self._row_limit = current_app.config["SQL_ROW_LIMIT"]
        self._conn = self._connect()

    def _connect(self) -> duckdb.DuckDBPyConnection:
        self._validate_config()

        conn = duckdb.connect()

        conn.execute("INSTALL delta;")
        conn.execute("LOAD delta;")
        conn.execute("INSTALL azure;")
        conn.execute("LOAD azure;")

        escaped_connection_string = self._build_azure_connection_string().replace("'", "''")

        conn.execute(f"""
            CREATE OR REPLACE SECRET azure_secret (
                TYPE AZURE,
                CONNECTION_STRING '{escaped_connection_string}'
            )
        """)

        for table_name in GOLD_TABLES:
            path = f"{self._gold_base.rstrip('/')}/{table_name}"
            conn.execute(f"""
                CREATE OR REPLACE VIEW {table_name} AS
                SELECT * FROM delta_scan('{path}')
            """)
            logger.info("Registered DuckDB view for Gold table: %s", table_name)

        return conn

    def execute_query(self, sql_text: str) -> dict[str, Any]:
        safe_sql = self._apply_row_limit(sql_text)
        logger.info("Executing SQL through DuckDB Delta client")

        try:
            result = self._conn.execute(safe_sql)
            columns = [desc[0] for desc in result.description]
            rows = [list(row) for row in result.fetchall()]
            truncated = len(rows) >= self._row_limit

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "truncated": truncated,
            }
        except Exception as exc:
            logger.error("DuckDB query failed: %s", exc)
            raise DatabricksQueryError(str(exc)) from exc

    def test_connection(self) -> bool:
        try:
            result = self._conn.execute("SELECT 1 AS ping").fetchall()
            return len(result) > 0
        except Exception as exc:
            logger.warning("DuckDB connection test failed: %s", exc)
            return False

    def _apply_row_limit(self, sql_text: str) -> str:
        upper = sql_text.strip().upper()

        if upper.startswith("SELECT") and "LIMIT" not in upper:
            return f"{sql_text.rstrip(';')} LIMIT {self._row_limit}"

        return sql_text

    def _validate_config(self) -> None:
        missing = []

        if not self._account:
            missing.append("AZURE_STORAGE_ACCOUNT_NAME")
        if not self._key:
            missing.append("AZURE_STORAGE_ACCOUNT_KEY")
        if not self._gold_base:
            missing.append("ADLS_GOLD_BASE")

        if missing:
            raise DatabricksQueryError(
                "Missing required configuration: " + ", ".join(missing)
            )

    def _build_azure_connection_string(self) -> str:
        return (
            "DefaultEndpointsProtocol=https;"
            f"AccountName={self._account};"
            f"AccountKey={self._key};"
            "EndpointSuffix=core.windows.net"
        )


class DatabricksQueryError(Exception):
    pass