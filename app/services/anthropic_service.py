"""
Anthropic LLM Service
Handles multi-turn conversation with Claude to:
  1. Generate SQL from natural language
  2. Narrate query results back to the user
"""
from __future__ import annotations

import logging
from typing import Any

import anthropic
from flask import current_app

from app.utils.schema_context import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AnthropicService:
    """Stateless wrapper around the Anthropic Messages API."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(
            api_key=current_app.config["ANTHROPIC_API_KEY"]
        )
        self._model: str = current_app.config["ANTHROPIC_MODEL"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_sql(self, user_message: str, history: list[dict]) -> str:
        """
        Send the user message + conversation history to Claude.
        Expects Claude to return a SQL statement in a ```sql block.
        Returns the raw LLM text response.
        """
        messages = self._build_messages(history, user_message)
        return self._call(messages)

    def narrate_results(
        self,
        user_question: str,
        sql_executed: str,
        results: dict[str, Any],
        history: list[dict],
    ) -> str:
        """
        Send query results back to Claude and ask it to narrate
        the findings in clear business language.
        """
        result_summary = (
            f"The following SQL was executed:\n```sql\n{sql_executed}\n```\n\n"
            f"It returned {results['row_count']} rows"
            f"{' (truncated)' if results['truncated'] else ''}.\n\n"
            f"Columns: {results['columns']}\n\n"
            f"First rows (up to 20):\n{results['rows'][:20]}\n\n"
            f"Now narrate these results for the user who asked: \"{user_question}\""
        )

        messages = self._build_messages(history, result_summary)
        return self._call(messages)

    def answer_direct(self, user_message: str, history: list[dict]) -> str:
        """
        For non-data questions (greetings, clarifications, off-topic).
        """
        messages = self._build_messages(history, user_message)
        return self._call(messages)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_messages(
        self, history: list[dict], new_user_message: str
    ) -> list[dict]:
        messages = list(history)
        messages.append({"role": "user", "content": new_user_message})
        return messages

    def _call(self, messages: list[dict]) -> str:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s", exc)
            raise AnthropicServiceError(str(exc)) from exc


class AnthropicServiceError(Exception):
    """Raised when the Anthropic API call fails."""
