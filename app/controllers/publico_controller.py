"""Controlador de publico: lógica de cada petición (MVC). Las URLs se declaran en app/routes/publico.py."""

import os
import secrets

from flask import current_app, request, send_from_directory

from app import repositories as repo
from app.models import (
    AporteProyecto, ComentarioPublicacion, CompartidoPublicacion, Logro,
    ParticipacionEvento, Postulacion, Publicacion, ReaccionPublicacion,
    SeguidorSemillero, SemilleroIntegrante, VisualizacionPublicacion,
    ROLES, utcnow
)
from app.schemas.serializers import (
    convocatoria_row, evento_row, logro_row, proyecto_row, publicacion_row,
    semillero_row, user_public
)
from app.services import indicadores
from app.services.acciones import guardar_evidencias
from app.services.gamificacion import (
    nivel_de, ranking_estudiantes, ranking_semilleros, semilleros_activos_de,
    xp_siguiente, xp_total
)
from app.utils.helpers import (
    body, current_user, fail, iso, log, notify, notify_many, ok,
    optional_user, text
)


def _uid(user):
    return user.id if user else None


# ------------------------------------------------------------------
# Catálogos e indicadores públicos
# ------------------------------------------------------------------

def catalogos():
    faculties = []
    for faculty in repo.facultades.activas():
        programs = repo.programas.activos_de(faculty.id)
        faculties.append({
            "id": faculty.id,
            "nombre": faculty.nombre,
            "programas": [p.nombre for p in programs]
        })

    return ok({
        "facultades": faculties,
        "roles": ROLES,
        "tipos_logro": [{"nombre": t.nombre, "xp": t.xp} for t in repo.tipos_logro.ordenados()],
        "categorias": [c.nombre for c in repo.categorias.ordenadas()]
    })


def public_indicadores():
    return ok({
        "resumen": indicadores.resumen_global(),
        "por_facultad": indicadores.por_grupo("facultad")
    })


# ------------------------------------------------------------------
# Semilleros (RF-14)
# ------------------------------------------------------------------

def _semillero_public(sem, user):
    row = semillero_row(sem)
    if user:
        member = repo.integrantes.get((sem.id, user.id))
        row["mi_estado"] = member.estado if member else None
        row["siguiendo"] = repo.seguidores.get((sem.id, user.id)) is not None
    return row


def semilleros_search():
    user = optional_user()
    rows = repo.semilleros.buscar_activos(
        request.args.get("q", ""), request.args.get("facultad", "")
    )
    return ok([_semillero_public(s, user) for s in rows])


def semillero_detail(sem_id):
    user = optional_user()
    sem = repo.semilleros.get(sem_id)

    if not sem or sem.estado != "Activo":
        return fail("Semillero no encontrado", 404)

    members = repo.integrantes.activos_de_semillero(sem.id)
    member_ids = [m.usuario_id for m in members]

    publicaciones = repo.publicaciones.publicadas_de_semillero(sem.id, limite=20)
    proyectos = repo.proyectos.de_semillero(sem.id)
    logros = repo.logros.aprobados_de_usuarios(member_ids, limite=10)
    productos = repo.productos.aprobados_de_semillero(sem.id)

    integrantes = []
    for member in members:
        xp = xp_total(usuario_id=member.usuario_id)
        integrantes.append({
            "nombre": member.usuario.nombre,
            "programa": member.usuario.programa.nombre if member.usuario.programa else "",
            "xp": xp
        })
    integrantes.sort(key=lambda row: -row["xp"])

    row = _semillero_public(sem, user)
    row.update({
        "publicaciones": [publicacion_row(p, _uid(user)) for p in publicaciones],
        "proyectos": [proyecto_row(p) for p in proyectos],
        "integrantes": integrantes,
        "logros": [l.descripcion for l in logros] + [f"Producto: {p.titulo}" for p in productos]
    })
    return ok(row)


def solicitar_vinculacion(sem_id):
    me = current_user()
    sem = repo.semilleros.get(sem_id)

    if not sem or sem.estado != "Activo":
        return fail("Semillero no encontrado", 404)

    member = repo.integrantes.get((sem.id, me.id))

    if member and member.estado == "Activo":
        return fail("Ya eres integrante de este semillero", 409)
    if member and member.estado == "Pendiente":
        return fail("Ya tienes una solicitud pendiente", 409)

    if member:  # solicitud rechazada anteriormente: se reenvía
        member.estado = "Pendiente"
        member.fecha_solicitud = utcnow()
    else:
        repo.integrantes.add(SemilleroIntegrante(semillero_id=sem.id, usuario_id=me.id))

    if sem.docente_lider_id:
        notify(sem.docente_lider_id, "semillero",
               f"{me.nombre} solicitó vincularse a {sem.nombre}", "semillero", sem.id)

    log("VINCULACION_SOLICITADA", f"semillero={sem.id}")
    repo.commit()
    return ok({"mi_estado": "Pendiente"}, "Solicitud de vinculación enviada", 201)


def seguir(sem_id):
    me = current_user()
    sem = repo.semilleros.get(sem_id)

    if not sem or sem.estado != "Activo":
        return fail("Semillero no encontrado", 404)

    follow = repo.seguidores.get((sem.id, me.id))

    if request.method == "POST" and not follow:
        repo.seguidores.add(SeguidorSemillero(semillero_id=sem.id, usuario_id=me.id))
    elif request.method == "DELETE" and follow:
        repo.seguidores.delete(follow)

    repo.commit()
    return ok({"siguiendo": request.method == "POST"})


# ------------------------------------------------------------------
# Proyectos
# ------------------------------------------------------------------

def proyectos_public():
    user = optional_user()
    term = request.args.get("q", "").strip().lower()

    mine = set(semilleros_activos_de(user.id)) if user else set()

    rows = []
    for proyecto in repo.proyectos.de_semilleros_activos():
        if term and term not in proyecto.nombre.lower() and term not in proyecto.semillero.nombre.lower():
            continue
        row = proyecto_row(proyecto)
        row["puedo_aportar"] = proyecto.semillero_id in mine and proyecto.estado != "Finalizado"
        rows.append(row)

    return ok(rows)


def registrar_aporte(item_id):
    me = current_user()
    proyecto = repo.proyectos.get(item_id)

    if not proyecto:
        return fail("Proyecto no encontrado", 404)
    if proyecto.semillero_id not in semilleros_activos_de(me.id):
        return fail("Solo los integrantes del semillero pueden registrar aportes", 403)

    description = text(body(), "descripcion")
    if not description:
        return fail("Describe tu aporte")

    repo.aportes.add(AporteProyecto(proyecto_id=proyecto.id, usuario_id=me.id, descripcion=description))
    log("PROYECTO_APORTE", f"proyecto={proyecto.id}")
    repo.commit()
    return ok(message="Aporte registrado", status=201)


# ------------------------------------------------------------------
# Publicaciones y su interacción social
# ------------------------------------------------------------------

def publicaciones_public():
    user = optional_user()
    rows = repo.publicaciones.publicas(
        semillero_id=request.args.get("semillero_id", type=int),
        termino=request.args.get("q", "")
    )
    return ok([publicacion_row(p, _uid(user)) for p in rows])


def publicacion_detail(pub_id):
    user = optional_user()
    pub = repo.publicaciones.get(pub_id)

    if not pub or pub.estado != "Publicada":
        return fail("Publicación no encontrada", 404)

    repo.visualizaciones.add(VisualizacionPublicacion(publicacion_id=pub.id, usuario_id=_uid(user)))
    repo.commit()

    comments = repo.comentarios.de_publicacion(pub.id)

    row = publicacion_row(pub, _uid(user))
    row["lista_comentarios"] = [{
        "autor": c.usuario.nombre,
        "contenido": c.contenido,
        "fecha": c.fecha.strftime("%Y-%m-%d %H:%M")
    } for c in comments]
    return ok(row)


def publicaciones_create():
    """Un estudiante propone una publicación; queda «En revisión» hasta que su docente líder la publique."""
    me = current_user()
    data = body()
    title = text(data, "titulo")
    category = repo.categorias.por_nombre(text(data, "tipo"))

    sem_ids = semilleros_activos_de(me.id)
    sem_id = data.get("semillero_id") or (sem_ids[0] if sem_ids else None)

    if not title:
        return fail("El título es obligatorio")
    if not category:
        return fail("Tipo de publicación no válido")
    if not sem_id or int(sem_id) not in sem_ids:
        return fail("Debes ser integrante activo de un semillero para publicar", 403)

    pub = Publicacion(
        titulo=title, contenido=text(data, "contenido"), estado="En revisión",
        usuario_id=me.id, semillero_id=int(sem_id), categoria_id=category.id
    )
    repo.publicaciones.add(pub)
    repo.flush()

    error = guardar_evidencias("publicacion", pub.id, data)
    if error:
        repo.rollback()
        return fail(error)

    sem = repo.semilleros.get(pub.semillero_id)
    if sem and sem.docente_lider_id:
        notify(sem.docente_lider_id, "publicacion",
               f"{me.nombre} propuso la publicación «{pub.titulo}»", "publicacion", pub.id)

    log("PUBLICACION_CREADA", f"publicacion={pub.id}")
    repo.commit()
    return ok(publicacion_row(pub, me.id), "Publicación enviada a revisión del docente líder", 201)


def _published(pub_id):
    pub = repo.publicaciones.get(pub_id)
    return pub if pub and pub.estado == "Publicada" else None


def reaccionar(pub_id):
    me = current_user()
    pub = _published(pub_id)
    if not pub:
        return fail("Publicación no encontrada", 404)

    reaction = repo.reacciones.de(pub.id, me.id)

    if reaction:
        repo.reacciones.delete(reaction)
        reacted = False
    else:
        repo.reacciones.add(ReaccionPublicacion(publicacion_id=pub.id, usuario_id=me.id))
        reacted = True
        if pub.usuario_id != me.id:
            notify(pub.usuario_id, "interaccion", f"A {me.nombre} le gustó «{pub.titulo}»",
                   "publicacion", pub.id)

    repo.commit()
    return ok({
        "yo_reaccione": reacted,
        "reacciones": repo.reacciones.contar_de(pub.id)
    })


def comentar(pub_id):
    me = current_user()
    pub = _published(pub_id)
    if not pub:
        return fail("Publicación no encontrada", 404)

    content = text(body(), "contenido")
    if not content:
        return fail("Escribe un comentario")
    if len(content) > 1000:
        return fail("El comentario no puede superar 1000 caracteres")

    repo.comentarios.add(ComentarioPublicacion(publicacion_id=pub.id, usuario_id=me.id, contenido=content))

    if pub.usuario_id != me.id:
        notify(pub.usuario_id, "interaccion", f"{me.nombre} comentó «{pub.titulo}»",
               "publicacion", pub.id)

    repo.commit()
    return ok({"comentarios": repo.comentarios.contar_de(pub.id)},
              "Comentario publicado", 201)


def compartir(pub_id):
    me = current_user()
    pub = _published(pub_id)
    if not pub:
        return fail("Publicación no encontrada", 404)

    repo.compartidos.add(CompartidoPublicacion(publicacion_id=pub.id, usuario_id=me.id))
    repo.commit()
    return ok({
        "compartidos": repo.compartidos.contar_de(pub.id),
        "enlace": f"/?publicacion={pub.id}"
    })


# ------------------------------------------------------------------
# Eventos y convocatorias
# ------------------------------------------------------------------

def eventos_public():
    user = optional_user()
    rows = repo.eventos.recientes()
    return ok([evento_row(e, _uid(user)) for e in rows])


def participar(item_id):
    me = current_user()
    evento = repo.eventos.get(item_id)
    if not evento:
        return fail("Evento no encontrado", 404)

    record = repo.participaciones.get((evento.id, me.id))

    if request.method == "POST":
        if evento.estado != "Abierta":
            return fail("El evento está cerrado", 409)
        if not record:
            repo.participaciones.add(ParticipacionEvento(evento_id=evento.id, usuario_id=me.id))
        message = "Participación registrada"
    else:
        if record:
            repo.participaciones.delete(record)
        message = "Participación cancelada"

    repo.commit()
    return ok({"participo": request.method == "POST"}, message)


def convocatorias_public():
    user = optional_user()
    rows = repo.convocatorias.recientes()
    return ok([convocatoria_row(c, _uid(user)) for c in rows])


def postular(item_id):
    me = current_user()
    conv = repo.convocatorias.get(item_id)

    if not conv:
        return fail("Convocatoria no encontrada", 404)
    if conv.estado != "Abierta" or (conv.cierre and conv.cierre < utcnow().date()):
        return fail("La convocatoria ya está cerrada", 409)
    if repo.postulaciones.de(conv.id, me.id):
        return fail("Ya te postulaste a esta convocatoria", 409)

    if me.es_docente:
        sem = repo.semilleros.activo_de_lider(me.id)
        sem_id = sem.id if sem else None
    else:
        ids = semilleros_activos_de(me.id)
        sem_id = ids[0] if ids else None

    repo.postulaciones.add(Postulacion(
        convocatoria_id=conv.id, usuario_id=me.id, semillero_id=sem_id, nota=text(body(), "nota")
    ))
    log("POSTULACION", f"convocatoria={conv.id}")
    repo.commit()
    return ok(message="Postulación enviada", status=201)


# ------------------------------------------------------------------
# Ranking (RF-45, RF-46, RF-53)
# ------------------------------------------------------------------

def ranking():
    user = optional_user()
    published = repo.configuracion.get("ranking_publicado")

    if published and published.valor != "1" and not (user and user.es_admin):
        return ok({"publicado": False, "filas": []})

    kind = request.args.get("tipo", "semilleros")
    faculty = repo.facultades.por_nombre(request.args["facultad"]) if request.args.get("facultad") else None
    program = repo.programas.por_nombre(request.args["programa"]) if request.args.get("programa") else None

    if kind == "estudiantes":
        rows = ranking_estudiantes(faculty.id if faculty else None, program.id if program else None)
    else:
        rows = ranking_semilleros(faculty.id if faculty else None)

    return ok({"publicado": True, "filas": rows})


# ------------------------------------------------------------------
# Logros del estudiante
# ------------------------------------------------------------------

def mis_logros():
    rows = repo.logros.de_usuario(current_user().id)
    return ok([logro_row(l) for l in rows])


def registrar_logro():
    me = current_user()
    data = body()
    description = text(data, "descripcion")
    kind = repo.tipos_logro.por_nombre(text(data, "tipo"))

    if not description:
        return fail("La descripción es obligatoria")
    if not kind:
        return fail("Selecciona un tipo de logro válido")
    if not (data.get("evidencia") or data.get("archivo")):
        return fail("Adjunta una evidencia (enlace o archivo) antes de enviar el logro")

    logro = Logro(usuario_id=me.id, tipo_logro_id=kind.id, descripcion=description[:300])
    repo.logros.add(logro)
    repo.flush()

    error = guardar_evidencias("logro", logro.id, data)
    if error:
        repo.rollback()
        return fail(error)

    # Envío automático a validación (RF-38): docente líder responsable o, si no tiene, administradores
    leaders = []
    for sem_id in semilleros_activos_de(me.id):
        sem = repo.semilleros.get(sem_id)
        if sem and sem.docente_lider_id:
            leaders.append(sem.docente_lider_id)

    if not leaders:
        leaders = repo.usuarios.ids_admins_activos()

    notify_many(leaders, "logro", f"{me.nombre} registró un logro para validar: {logro.descripcion}",
                "logro", logro.id)
    log("LOGRO_REGISTRADO", f"logro={logro.id}")
    repo.commit()
    return ok(logro_row(logro), "Logro enviado a validación", 201)


# ------------------------------------------------------------------
# Hoja de vida investigativa (RF-12)
# ------------------------------------------------------------------

def hoja_de_vida():
    me = current_user()
    xp = xp_total(usuario_id=me.id)

    semilleros = []
    for member in repo.integrantes.activos_de_usuario(me.id):
        semilleros.append({"id": member.semillero_id, "nombre": member.semillero.nombre})

    logros = repo.logros.aprobados_de_usuario(me.id)

    badges = repo.usuario_insignias.de_usuario(me.id)

    participaciones = []
    for record in repo.participaciones.de_usuario(me.id):
        evento = repo.eventos.get(record.evento_id)
        participaciones.append({"evento": evento.nombre, "fecha": iso(evento.fecha)})

    return ok({
        "usuario": user_public(me),
        "xp": xp,
        "nivel": nivel_de(xp),
        "xpSiguiente": xp_siguiente(xp),
        "semilleros": semilleros,
        "logros": [logro_row(l) for l in logros],
        "insignias": [{"nombre": b.insignia.nombre, "descripcion": b.insignia.descripcion or "",
                       "fecha": iso(b.fecha.date())} for b in badges],
        "publicaciones": repo.publicaciones.contar_publicadas(usuario_id=me.id),
        "aportes": repo.aportes.contar_de_usuario(me.id),
        "participaciones": participaciones
    })


# ------------------------------------------------------------------
# Notificaciones (RF-47, RF-48)
# ------------------------------------------------------------------

def notificaciones():
    rows = repo.notificaciones.recientes_de(current_user().id, 100)
    return ok([{
        "id": n.id,
        "tipo": n.tipo,
        "mensaje": n.mensaje,
        "leida": n.leida,
        "estado": "Leída" if n.leida else "Nueva",
        "fecha": n.fecha.strftime("%Y-%m-%d %H:%M")
    } for n in rows])


def notificacion_leer(item_id):
    notification = repo.notificaciones.get(item_id)

    if not notification or notification.usuario_id != current_user().id:
        return fail("Notificación no encontrada", 404)

    notification.leida = True
    repo.commit()
    return ok(message="Notificación leída")


def notificaciones_leer_todas():
    repo.notificaciones.marcar_todas_leidas(current_user().id)
    repo.commit()
    return ok(message="Notificaciones marcadas como leídas")


# ------------------------------------------------------------------
# Archivos de evidencia (RNF-05: validación de formato y tamaño)
# ------------------------------------------------------------------

FIRMAS = {
    "pdf": (b"%PDF",),
    "png": (b"\x89PNG",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "docx": (b"PK\x03\x04",),
    "pptx": (b"PK\x03\x04",),
    "xlsx": (b"PK\x03\x04",)
}


def subir_archivo():
    file = request.files.get("file")

    if not file or not file.filename:
        return fail("Selecciona un archivo")

    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in FIRMAS:
        return fail("Formato no permitido. Usa: " + ", ".join(sorted(FIRMAS)))

    content = file.read(current_app.config["MAX_UPLOAD_BYTES"] + 1)

    if len(content) > current_app.config["MAX_UPLOAD_BYTES"]:
        return fail("El archivo supera el tamaño máximo permitido (5 MB)", 413)
    if not any(content.startswith(signature) for signature in FIRMAS[extension]):
        return fail("El contenido del archivo no corresponde a su formato")

    name = f"{secrets.token_hex(16)}.{extension}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)

    with open(os.path.join(folder, name), "wb") as handle:
        handle.write(content)

    log("ARCHIVO_SUBIDO", f"archivo={name}")
    repo.commit()
    return ok({"url": f"/api/files/{name}"}, "Archivo cargado", 201)


def descargar_archivo(name):
    response = send_from_directory(current_app.config["UPLOAD_FOLDER"], name, as_attachment=True)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
