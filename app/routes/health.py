"""
Health Blueprint — /health
Checks Databricks connectivity.
"""
from flask import Blueprint, jsonify
from app.rest_clients.databricks_client import DatabricksClient

health_bp = Blueprint("health", __name__)


@health_bp.route("/")
def health():
    db = DatabricksClient()
    connected = db.test_connection()
    status = "ok" if connected else "degraded"
    return jsonify({
        "status": status,
        "databricks": "connected" if connected else "unreachable",
    }), 200 if connected else 503
