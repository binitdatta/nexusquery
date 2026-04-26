"""
Home Blueprint — /
Serves the landing page and the chat page.
"""
from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    return render_template("home.html")


@home_bp.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")
