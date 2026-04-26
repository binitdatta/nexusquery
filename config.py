"""
NexusQuery Configuration
Reads from environment variables / .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    # Azure Databricks SQL Warehouse
    DATABRICKS_SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME", "")
    DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "")
    DATABRICKS_ACCESS_TOKEN = os.getenv("DATABRICKS_ACCESS_TOKEN", "")

    # Azure Storage / ADLS Gen2
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "")
    ADLS_GOLD_BASE = os.getenv("ADLS_GOLD_BASE", "")

    # Chat settings
    MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "20"))
    SQL_ROW_LIMIT = int(os.getenv("SQL_ROW_LIMIT", "500"))