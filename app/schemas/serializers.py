"""Conversión de modelos a los diccionarios que consume el frontend."""

from app import repositories as repo
from app.services.gamificacion import nivel_de, xp_siguiente, xp_total
from app.utils.helpers import iso


def user_public(user):
    return {
        "id": user.id,
        "name": user.nombre,
        "email": user.email,
        "role": user.rol.nombre,
        "faculty": user.facultad.nombre if user.facultad else "",
        "program": user.programa.nombre if user.programa else "",
        "estado": user.estado,
        "telefono": user.telefono or "",
        "biografia": user.biografia or ""
    }


def user_row(user):
    return {
        "id": user.id,
        "nombre": user.nombre,
        "correo": user.email,
        "facultad": user.facultad.nombre if user.facultad else "",
        "programa": user.programa.nombre if user.programa else "",
        "rol": user.rol.nombre,
        "estado": user.estado,
        "cuenta": user.tipo_cuenta,
        "fecha": iso(user.fecha_registro.date())
    }


def semillero_row(sem):
    xp = xp_total(semillero_id=sem.id)
    return {
        "id": sem.id,
        "nombre": sem.nombre,
        "descripcion": sem.descripcion or "",
        "linea": sem.linea or "",
        "facultad": sem.facultad.nombre if sem.facultad else "",
        "lider": sem.lider.nombre if sem.lider else "",
        "integrantes": repo.integrantes.contar_activos(sem.id),
        "xp": xp,
        "nivel": nivel_de(xp),
        "xpSiguiente": xp_siguiente(xp),
        "estado": sem.estado
    }


def proyecto_row(proyecto):
    return {
        "id": proyecto.id,
        "nombre": proyecto.nombre,
        "descripcion": proyecto.descripcion or "",
        "semillero": proyecto.semillero.nombre,
        "semillero_id": proyecto.semillero_id,
        "estado": proyecto.estado,
        "avance": proyecto.avance,
        "inicio": iso(proyecto.fecha_inicio)
    }


def evento_row(evento, user_id=None):
    row = {
        "id": evento.id,
        "nombre": evento.nombre,
        "descripcion": evento.descripcion or "",
        "fecha": iso(evento.fecha),
        "modalidad": evento.modalidad,
        "semillero": evento.semillero.nombre if evento.semillero else "",
        "estado": evento.estado,
        "participantes": repo.participaciones.contar_de_evento(evento.id)
    }

    if user_id:
        row["participo"] = repo.participaciones.get((evento.id, user_id)) is not None

    return row


def convocatoria_row(conv, user_id=None):
    row = {
        "id": conv.id,
        "titulo": conv.titulo,
        "descripcion": conv.descripcion or "",
        "cierre": iso(conv.cierre),
        "estado": conv.estado,
        "postulaciones": repo.postulaciones.contar_de_convocatoria(conv.id)
    }

    if user_id:
        row["postulado"] = repo.postulaciones.de(conv.id, user_id) is not None

    return row


def publicacion_row(pub, user_id=None):
    evidencias = repo.evidencias.de_publicacion(pub.id)

    row = {
        "id": pub.id,
        "titulo": pub.titulo,
        "contenido": pub.contenido or "",
        "tipo": pub.categoria.nombre,
        "semillero": pub.semillero.nombre if pub.semillero else "",
        "semillero_id": pub.semillero_id,
        "autor": pub.autor.nombre,
        "anio": pub.fecha.year,
        "fecha": iso(pub.fecha.date()),
        "estado": pub.estado,
        "reacciones": repo.reacciones.contar_de(pub.id),
        "comentarios": repo.comentarios.contar_de(pub.id),
        "compartidos": repo.compartidos.contar_de(pub.id),
        "vistas": repo.visualizaciones.contar_de(pub.id),
        "evidencias": [{"tipo": e.tipo, "url": e.url} for e in evidencias]
    }

    if user_id:
        row["yo_reaccione"] = repo.reacciones.de(pub.id, user_id) is not None

    return row


def logro_row(logro):
    evidencias = repo.evidencias.de_logro(logro.id)
    return {
        "id": logro.id,
        "descripcion": logro.descripcion,
        "usuario": logro.usuario.nombre,
        "tipo": logro.tipo.nombre,
        "xp": logro.tipo.xp,
        "estado": logro.estado,
        "observacion": logro.observacion or "",
        "fecha": iso(logro.fecha_registro.date()),
        "evidencias": [{"tipo": e.tipo, "url": e.url} for e in evidencias]
    }


def producto_row(producto):
    return {
        "id": producto.id,
        "titulo": producto.titulo,
        "tipo": producto.tipo,
        "descripcion": producto.descripcion or "",
        "semillero": producto.semillero.nombre,
        "estado": producto.estado,
        "fecha": iso(producto.fecha.date())
    }


def integrante_row(member):
    user = member.usuario
    return {
        "id": user.id,
        "nombre": user.nombre,
        "correo": user.email,
        "programa": user.programa.nombre if user.programa else "",
        "estado": member.estado,
        "desde": iso((member.fecha_aprobacion or member.fecha_solicitud).date())
    }
