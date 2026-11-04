"""Rutas de docente: solo mapean URL -> controlador (app/controllers/docente_controller.py)."""

from flask import Blueprint

from app.models import ROL_DOCENTE
from app.controllers import docente_controller as controller
from app.utils.helpers import auth_required


bp = Blueprint("docente", __name__, url_prefix="/api/docente")


@bp.before_request
@auth_required(ROL_DOCENTE)
def _only_docente():
    return None



@bp.post("/semillero")
def semillero_create():
    return controller.semillero_create()


@bp.get("/semillero")
def semillero_get():
    return controller.semillero_get()


@bp.put("/semillero")
def semillero_update():
    return controller.semillero_update()


@bp.get("/integrantes")
def integrantes_list():
    return controller.integrantes_list()


@bp.post("/integrantes")
def integrantes_add():
    return controller.integrantes_add()


@bp.patch("/integrantes/<int:user_id>")
def integrantes_resolve(user_id):
    return controller.integrantes_resolve(user_id)


@bp.delete("/integrantes/<int:user_id>")
def integrantes_remove(user_id):
    return controller.integrantes_remove(user_id)


@bp.get("/proyectos")
def proyectos_list():
    return controller.proyectos_list()


@bp.post("/proyectos")
def proyectos_create():
    return controller.proyectos_create()


@bp.put("/proyectos/<int:item_id>")
@bp.patch("/proyectos/<int:item_id>")
def proyectos_update(item_id):
    return controller.proyectos_update(item_id)


@bp.post("/proyectos/<int:item_id>/avances")
def proyectos_avance(item_id):
    return controller.proyectos_avance(item_id)


@bp.get("/publicaciones")
def publicaciones_list():
    return controller.publicaciones_list()


@bp.post("/publicaciones")
def publicaciones_create():
    return controller.publicaciones_create()


@bp.put("/publicaciones/<int:item_id>")
def publicaciones_update(item_id):
    return controller.publicaciones_update(item_id)


@bp.patch("/publicaciones/<int:item_id>")
def publicaciones_state(item_id):
    return controller.publicaciones_state(item_id)


@bp.delete("/publicaciones/<int:item_id>")
def publicaciones_delete(item_id):
    return controller.publicaciones_delete(item_id)


@bp.get("/eventos")
def eventos_list():
    return controller.eventos_list()


@bp.post("/eventos")
def eventos_create():
    return controller.eventos_create()


@bp.put("/eventos/<int:item_id>")
def eventos_update(item_id):
    return controller.eventos_update(item_id)


@bp.delete("/eventos/<int:item_id>")
def eventos_delete(item_id):
    return controller.eventos_delete(item_id)


@bp.get("/logros")
def logros_list():
    return controller.logros_list()


@bp.post("/logros")
def logros_create():
    return controller.logros_create()


@bp.patch("/logros/<int:item_id>")
def logros_resolve(item_id):
    return controller.logros_resolve(item_id)


@bp.get("/productos")
def productos_list():
    return controller.productos_list()


@bp.post("/productos")
def productos_create():
    return controller.productos_create()


@bp.delete("/productos/<int:item_id>")
def productos_delete(item_id):
    return controller.productos_delete(item_id)
