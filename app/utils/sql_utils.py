"""
SQL extraction and validation utilities.
"""
from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# Dangerous statements that must never execute
_FORBIDDEN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER|TRUNCATE|REPLACE|MERGE)\b",
    re.IGNORECASE,
)


def extract_sql(text: str) -> str | None:
    """
    Extract SQL from an LLM response that may contain a ```sql block.
    Returns the raw SQL string or None if not found.
    """
    # Try fenced code block first
    match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback: look for a SELECT statement
    match = re.search(r"(SELECT\s+.+)", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def is_safe_sql(sql_text: str) -> bool:
    """Return True only if the SQL contains no dangerous statements."""
    if _FORBIDDEN.search(sql_text):
        logger.warning("Blocked unsafe SQL: %s", sql_text[:200])
        return False
    return True


def format_results_as_markdown(columns: list[str], rows: list[list]) -> str:
    """Convert columnar query results to a Markdown table string."""
    if not rows:
        return "_No results returned._"

    header = " | ".join(columns)
    separator = " | ".join(["---"] * len(columns))
    data_rows = [" | ".join(str(v) for v in row) for row in rows]

    return "\n".join([header, separator] + data_rows)
