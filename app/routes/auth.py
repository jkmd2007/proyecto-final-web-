"""Rutas de auth: solo mapean URL -> controlador (app/controllers/auth_controller.py)."""

from flask import Blueprint

from app.controllers import auth_controller as controller
from app.utils.helpers import auth_required


bp = Blueprint("auth", __name__, url_prefix="/api/auth")



@bp.post("/register")
def register():
    return controller.register()


@bp.post("/login")
def login():
    return controller.login()


@bp.post("/logout")
@auth_required()
def logout():
    return controller.logout()


@bp.post("/recover")
def recover():
    return controller.recover()


@bp.post("/reset")
def reset():
    return controller.reset()


@bp.get("/me")
@auth_required()
def me():
    return controller.me()


@bp.put("/me")
@auth_required()
def update_me():
    return controller.update_me()


@bp.post("/password")
@auth_required()
def change_password():
    return controller.change_password()
