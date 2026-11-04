"""Controlador de la vista web: entrega la SPA (templates = Vista)."""

from flask import render_template


def index():
    """Página principal."""
    return render_template("index.html")
