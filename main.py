"""
NexusQuery — WSGI entry point.

Development:
    python main.py

Production (gunicorn):
    gunicorn -c gunicorn.conf.py "main:app"
"""
from app import create_app

# 'app' is the WSGI callable gunicorn looks for
app = create_app()

if __name__ == "__main__":
    # Direct run only — gunicorn does not use this block
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])