"""
Chat Blueprint — /chat
Handles the AJAX chat endpoint used by the frontend.
"""
from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request, session

from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/message", methods=["POST"])
def message():
    """
    POST /chat/message
    Body: { "message": "user text" }
    Response: {
        "assistant_message": str,
        "sql_generated": str | null,
        "row_count": int | null,
        "truncated": bool,
        "error": str | null
    }
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Maintain conversation history in server-side session
    history: list[dict] = session.get("chat_history", [])

    service = ChatService()
    turn_result = service.process_turn(user_message, history)

    # Append this turn to history
    history.append({"role": "user", "content": user_message})
    history.append({
        "role": "assistant",
        "content": turn_result["assistant_message"]
    })

    # Trim history to max configured turns (2 messages per turn)
    from flask import current_app
    max_turns = current_app.config["MAX_HISTORY_TURNS"]
    if len(history) > max_turns * 2:
        history = history[-(max_turns * 2):]

    session["chat_history"] = history

    query_results = turn_result.get("query_results")
    return jsonify({
        "assistant_message": turn_result["assistant_message"],
        "sql_generated": turn_result.get("sql_generated"),
        "row_count": query_results["row_count"] if query_results else None,
        "truncated": query_results["truncated"] if query_results else False,
        "error": turn_result.get("error"),
    })


@chat_bp.route("/reset", methods=["POST"])
def reset():
    """POST /chat/reset — clear conversation history."""
    session.pop("chat_history", None)
    return jsonify({"status": "ok"})
