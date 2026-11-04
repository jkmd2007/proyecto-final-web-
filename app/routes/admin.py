"""Rutas de admin: solo mapean URL -> controlador (app/controllers/admin_controller.py)."""

from flask import Blueprint

from app.models import ROL_ADMIN
from app.controllers import admin_controller as controller
from app.utils.helpers import auth_required


bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.before_request
@auth_required(ROL_ADMIN)
def _only_admin():
    """Todas las rutas de /api/admin exigen rol Administrador."""
    return None



@bp.get("/users")
def users_list():
    return controller.users_list()


@bp.post("/users")
def users_create():
    return controller.users_create()


@bp.put("/users/<int:user_id>")
def users_update(user_id):
    return controller.users_update(user_id)


@bp.patch("/users/<int:user_id>")
def users_state(user_id):
    return controller.users_state(user_id)


@bp.patch("/users/<int:user_id>/role")
def users_role(user_id):
    return controller.users_role(user_id)


@bp.patch("/users/<int:user_id>/approve")
def users_approve(user_id):
    return controller.users_approve(user_id)


@bp.patch("/users/<int:user_id>/reject")
def users_reject(user_id):
    return controller.users_reject(user_id)


@bp.get("/semilleros")
def semilleros_list():
    return controller.semilleros_list()


@bp.post("/semilleros")
def semilleros_create():
    return controller.semilleros_create()


@bp.put("/semilleros/<int:sem_id>")
def semilleros_update(sem_id):
    return controller.semilleros_update(sem_id)


@bp.patch("/semilleros/<int:sem_id>")
def semilleros_state(sem_id):
    return controller.semilleros_state(sem_id)


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


@bp.delete("/proyectos/<int:item_id>")
def proyectos_delete(item_id):
    return controller.proyectos_delete(item_id)


@bp.get("/eventos")
def eventos_list():
    return controller.eventos_list()


@bp.post("/eventos")
def eventos_create():
    return controller.eventos_create()


@bp.put("/eventos/<int:item_id>")
@bp.patch("/eventos/<int:item_id>")
def eventos_update(item_id):
    return controller.eventos_update(item_id)


@bp.delete("/eventos/<int:item_id>")
def eventos_delete(item_id):
    return controller.eventos_delete(item_id)


@bp.get("/convocatorias")
def convocatorias_list():
    return controller.convocatorias_list()


@bp.post("/convocatorias")
def convocatorias_create():
    return controller.convocatorias_create()


@bp.put("/convocatorias/<int:item_id>")
@bp.patch("/convocatorias/<int:item_id>")
def convocatorias_update(item_id):
    return controller.convocatorias_update(item_id)


@bp.delete("/convocatorias/<int:item_id>")
def convocatorias_delete(item_id):
    return controller.convocatorias_delete(item_id)


@bp.get("/publicaciones")
def publicaciones_list():
    return controller.publicaciones_list()


@bp.patch("/publicaciones/<int:item_id>")
def publicaciones_state(item_id):
    return controller.publicaciones_state(item_id)


@bp.delete("/publicaciones/<int:item_id>")
def publicaciones_delete(item_id):
    return controller.publicaciones_delete(item_id)


@bp.get("/logros")
def logros_list():
    return controller.logros_list()


@bp.patch("/logros/<int:item_id>")
def logros_resolve(item_id):
    return controller.logros_resolve(item_id)


@bp.get("/productos")
def productos_list():
    return controller.productos_list()


@bp.patch("/productos/<int:item_id>")
def productos_resolve(item_id):
    return controller.productos_resolve(item_id)


@bp.get("/facultades")
def facultades_list():
    return controller.facultades_list()


@bp.post("/facultades")
def facultades_create():
    return controller.facultades_create()


@bp.put("/facultades/<int:item_id>")
@bp.patch("/facultades/<int:item_id>")
def facultades_update(item_id):
    return controller.facultades_update(item_id)


@bp.get("/programas")
def programas_list():
    return controller.programas_list()


@bp.post("/programas")
@bp.put("/programas/<int:item_id>")
@bp.patch("/programas/<int:item_id>")
def programas_save(item_id=None):
    return controller.programas_save(item_id)


@bp.get("/bitacora")
def bitacora_list():
    return controller.bitacora_list()


@bp.get("/indicadores")
def indicadores_list():
    return controller.indicadores_list()


@bp.get("/reportes/<tipo>")
def reportes(tipo):
    return controller.reportes(tipo)


@bp.get("/config/ranking")
def ranking_config():
    return controller.ranking_config()


@bp.put("/config/ranking")
def ranking_publish():
    return controller.ranking_publish()
