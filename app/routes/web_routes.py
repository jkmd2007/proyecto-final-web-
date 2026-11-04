"""Rutas de la vista web: solo mapean URL -> controlador."""

from flask import Blueprint

from app.controllers import web_controller as controller


web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def index():
    return controller.index()
