"""
Chat Service
Orchestrates the full NL → SQL → Execute → Narrate pipeline.
"""
from __future__ import annotations

import logging
from typing import Any

from app.rest_clients.databricks_client import DatabricksClient, DatabricksQueryError
from app.services.anthropic_service import AnthropicService, AnthropicServiceError
from app.utils.sql_utils import extract_sql, is_safe_sql

logger = logging.getLogger(__name__)


class ChatService:
    """
    Orchestrates a single chat turn:
      1. Ask Anthropic to generate SQL
      2. Extract and validate the SQL
      3. Execute against Databricks
      4. Ask Anthropic to narrate the results
    """

    def __init__(self) -> None:
        self._llm = AnthropicService()
        self._db = DatabricksClient()

    def process_turn(
        self, user_message: str, history: list[dict]
    ) -> dict[str, Any]:
        """
        Process one conversation turn.

        Returns:
            {
                "assistant_message": str,    # text shown to user
                "sql_generated": str | None, # SQL that was generated
                "query_results": dict | None,# raw results from Databricks
                "error": str | None          # error message if any
            }
        """
        result: dict[str, Any] = {
            "assistant_message": "",
            "sql_generated": None,
            "query_results": None,
            "error": None,
        }

        try:
            # Step 1 — ask LLM to generate SQL
            llm_response = self._llm.get_sql(user_message, history)
            sql_text = extract_sql(llm_response)

            if not sql_text:
                # LLM returned a conversational answer, not SQL
                result["assistant_message"] = llm_response
                return result

            if not is_safe_sql(sql_text):
                result["assistant_message"] = (
                    "⚠️ The generated SQL contained unsafe operations and was blocked."
                )
                result["error"] = "Unsafe SQL blocked"
                return result

            result["sql_generated"] = sql_text

            # Step 2 — execute SQL against Databricks
            query_results = self._db.execute_query(sql_text)
            result["query_results"] = query_results

            # Step 3 — ask LLM to narrate the results
            narration = self._llm.narrate_results(
                user_question=user_message,
                sql_executed=sql_text,
                results=query_results,
                history=history,
            )
            result["assistant_message"] = narration

        except DatabricksQueryError as exc:
            logger.error("Databricks error in chat turn: %s", exc)
            result["error"] = str(exc)
            result["assistant_message"] = (
                f"⚠️ Databricks query failed: {exc}\n\n"
                "Please check that your cluster is running and the SQL is valid."
            )

        except AnthropicServiceError as exc:
            logger.error("Anthropic error in chat turn: %s", exc)
            result["error"] = str(exc)
            result["assistant_message"] = (
                f"⚠️ AI service error: {exc}"
            )

        except Exception as exc:
            logger.exception("Unexpected error in chat turn")
            result["error"] = str(exc)
            result["assistant_message"] = (
                "⚠️ An unexpected error occurred. Please try again."
            )

        return result
