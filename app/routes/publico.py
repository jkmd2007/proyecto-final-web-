"""Rutas de publico: solo mapean URL -> controlador (app/controllers/publico_controller.py)."""

from flask import Blueprint

from app.models import ROL_DOCENTE, ROL_ESTUDIANTE
from app.controllers import publico_controller as controller
from app.utils.helpers import auth_required


bp = Blueprint("api", __name__, url_prefix="/api")



@bp.get("/catalogos")
def catalogos():
    return controller.catalogos()


@bp.get("/public/indicadores")
def public_indicadores():
    return controller.public_indicadores()


@bp.get("/public/semilleros")
def semilleros_search():
    return controller.semilleros_search()


@bp.get("/public/semilleros/<int:sem_id>")
def semillero_detail(sem_id):
    return controller.semillero_detail(sem_id)


@bp.post("/semilleros/<int:sem_id>/vinculacion")
@auth_required(ROL_ESTUDIANTE)
def solicitar_vinculacion(sem_id):
    return controller.solicitar_vinculacion(sem_id)


@bp.route("/semilleros/<int:sem_id>/seguir", methods=["POST", "DELETE"])
@auth_required()
def seguir(sem_id):
    return controller.seguir(sem_id)


@bp.get("/public/proyectos")
def proyectos_public():
    return controller.proyectos_public()


@bp.post("/proyectos/<int:item_id>/aportes")
@auth_required(ROL_ESTUDIANTE)
def registrar_aporte(item_id):
    return controller.registrar_aporte(item_id)


@bp.get("/public/publicaciones")
def publicaciones_public():
    return controller.publicaciones_public()


@bp.get("/public/publicaciones/<int:pub_id>")
def publicacion_detail(pub_id):
    return controller.publicacion_detail(pub_id)


@bp.post("/publicaciones")
@auth_required(ROL_ESTUDIANTE)
def publicaciones_create():
    return controller.publicaciones_create()


@bp.post("/publicaciones/<int:pub_id>/reaccion")
@auth_required()
def reaccionar(pub_id):
    return controller.reaccionar(pub_id)


@bp.post("/publicaciones/<int:pub_id>/comentarios")
@auth_required()
def comentar(pub_id):
    return controller.comentar(pub_id)


@bp.post("/publicaciones/<int:pub_id>/compartir")
@auth_required()
def compartir(pub_id):
    return controller.compartir(pub_id)


@bp.get("/public/eventos")
def eventos_public():
    return controller.eventos_public()


@bp.route("/eventos/<int:item_id>/participar", methods=["POST", "DELETE"])
@auth_required()
def participar(item_id):
    return controller.participar(item_id)


@bp.get("/convocatorias")
def convocatorias_public():
    return controller.convocatorias_public()


@bp.post("/convocatorias/<int:item_id>/postulaciones")
@auth_required(ROL_ESTUDIANTE, ROL_DOCENTE)
def postular(item_id):
    return controller.postular(item_id)


@bp.get("/public/ranking")
def ranking():
    return controller.ranking()


@bp.get("/me/logros")
@auth_required(ROL_ESTUDIANTE)
def mis_logros():
    return controller.mis_logros()


@bp.post("/me/logros")
@auth_required(ROL_ESTUDIANTE)
def registrar_logro():
    return controller.registrar_logro()


@bp.get("/me/cv")
@auth_required()
def hoja_de_vida():
    return controller.hoja_de_vida()


@bp.get("/me/notificaciones")
@auth_required()
def notificaciones():
    return controller.notificaciones()


@bp.patch("/notificaciones/<int:item_id>")
@auth_required()
def notificacion_leer(item_id):
    return controller.notificacion_leer(item_id)


@bp.post("/notificaciones/leer-todas")
@auth_required()
def notificaciones_leer_todas():
    return controller.notificaciones_leer_todas()


@bp.post("/uploads")
@auth_required()
def subir_archivo():
    return controller.subir_archivo()


@bp.get("/files/<path:name>")
def descargar_archivo(name):
    return controller.descargar_archivo(name)
