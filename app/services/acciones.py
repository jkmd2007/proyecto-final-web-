"""Acciones de negocio compartidas entre rutas (publicar, borrar en cascada)."""

from app import repositories as repo
from app.utils.helpers import log, notify, notify_many


def publicar(pub, actor):
    """Publica el contenido y notifica a los seguidores del semillero (RF-27)."""
    pub.estado = "Publicada"

    destinatarios = []
    if pub.semillero_id:
        destinatarios = repo.seguidores.ids_de_semillero(pub.semillero_id)

    destinatarios = [uid for uid in destinatarios if uid != pub.usuario_id]
    notify_many(destinatarios, "publicacion", f"Nueva publicación: {pub.titulo}", "publicacion", pub.id)

    if pub.usuario_id != actor.id:
        notify(pub.usuario_id, "publicacion", f"Tu publicación «{pub.titulo}» fue publicada",
               "publicacion", pub.id)

    log("PUBLICACION_PUBLICADA", f"publicacion={pub.id}", actor)


def borrar_publicacion(pub):
    repo.publicaciones.eliminar(pub)


def borrar_proyecto(proyecto):
    repo.proyectos.eliminar(proyecto)


def borrar_evento(evento):
    repo.eventos.eliminar(evento)


def borrar_convocatoria(conv):
    repo.convocatorias.eliminar(conv)


# ------------------------------------------------------------------
# Evidencias (RF-25, RF-37)
# ------------------------------------------------------------------

def evidencia_valida(url):
    """Solo enlaces http(s) o archivos subidos al propio sistema."""
    return bool(url) and (
        url.startswith("https://") or url.startswith("http://") or url.startswith("/api/files/")
    ) and len(url) <= 500


def guardar_evidencias(destino, item_id, data):
    """
    Guarda el enlace ('evidencia') y/o el archivo subido ('archivo').
    destino: "publicacion" o "logro". Devuelve un mensaje de error o None.
    """
    agregar = {
        "publicacion": repo.evidencias.agregar_a_publicacion,
        "logro": repo.evidencias.agregar_a_logro,
    }[destino]

    for key, tipo in (("evidencia", "enlace"), ("archivo", "archivo")):
        url = str(data.get(key) or "").strip()

        if not url:
            continue
        if not evidencia_valida(url):
            return "La evidencia debe ser un enlace http(s) o un archivo subido"

        agregar(item_id, tipo, url)

    return None
