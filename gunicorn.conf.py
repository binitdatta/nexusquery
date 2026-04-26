"""
Gunicorn configuration for NexusQuery.
Run: gunicorn -c gunicorn.conf.py "main:app"
"""
import multiprocessing

# Server socket
bind = "0.0.0.0:8098"

# Worker processes — single worker on Mac POC to avoid forking issues
# In production Linux: workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
worker_class = "sync"
threads = 4

# Timeouts
timeout = 120          # generous — Databricks cold queries can be slow
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"        # stdout
errorlog  = "-"        # stderr
loglevel  = "info"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'

# Reload on code change (dev only — remove in production)
reload = True
reload_extra_files = [
    "config.py",
    "app/utils/schema_context.py",
]

# Process naming
proc_name = "nexusquery"