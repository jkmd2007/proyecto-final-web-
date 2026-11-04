"""Controlador de admin: lógica de cada petición (MVC). Las URLs se declaran en app/routes/admin.py."""

import secrets

from flask import current_app, request

from app import repositories as repo
from app.models import (
    Convocatoria, Evento, Facultad, Programa, Proyecto, Semillero, Usuario,
    ROL_ADMIN, utcnow
)
from app.controllers.auth_controller import resolve_academic
from app.schemas.serializers import (
    convocatoria_row, evento_row, logro_row, producto_row, proyecto_row,
    publicacion_row, semillero_row, user_row
)
from app.services import indicadores
from app.services.acciones import (
    borrar_convocatoria, borrar_evento, borrar_proyecto, borrar_publicacion,
    publicar
)
from app.services.gamificacion import XP_PRODUCTO, evaluar_insignias_semillero, resolver_logro
from app.services.mailer import send_mail
from app.utils.helpers import (
    body, csv_response, current_user, fail, log, notify, notify_many, ok,
    parse_date, text
)


def _not_found(label):
    return fail(f"{label} no encontrado", 404)


# ------------------------------------------------------------------
# Usuarios y solicitudes
# ------------------------------------------------------------------

def _active_admins():
    return repo.usuarios.contar_admins_activos()


def _guard_admin_change(user, new_role=None, new_state=None):
    """Impide autobloquearse o dejar el sistema sin administradores."""
    me = current_user()
    demoting = new_role is not None and new_role != ROL_ADMIN
    disabling = new_state is not None and new_state != "Activo"

    if user.id == me.id and (demoting or disabling):
        return "No puedes cambiar tu propio rol ni desactivar tu propia cuenta"

    if user.es_admin and user.estado == "Activo" and (demoting or disabling) and _active_admins() <= 1:
        return "Debe existir al menos un administrador activo"

    return None


def _role(name):
    return repo.roles.por_nombre(name)


def users_list():
    return ok([user_row(user) for user in repo.usuarios.recientes()])


def users_create():
    data = body()
    name = text(data, "nombre")
    email = text(data, "correo").lower()
    role = _role(text(data, "rol"))

    if not name or "@" not in email:
        return fail("Nombre y correo válido son obligatorios")
    if not role:
        return fail("Rol no válido")
    if repo.usuarios.por_email(email):
        return fail("Ya existe un usuario con ese correo", 409)

    faculty, program, error = resolve_academic(text(data, "facultad"), text(data, "programa"))
    if error:
        return fail(error)

    state = text(data, "estado", "Activo")
    if state not in ("Activo", "Inactivo"):
        return fail("Estado no válido")

    password = f"Riul{secrets.token_hex(3)}A1"
    domain = current_app.config["INSTITUTIONAL_DOMAIN"]

    user = Usuario(
        nombre=name, email=email, estado=state, rol_id=role.id,
        tipo_cuenta="Institucional" if email.endswith("@" + domain) else "Externa",
        facultad_id=faculty.id if faculty else None,
        programa_id=program.id if program else None
    )
    user.set_password(password)
    repo.usuarios.add(user)
    repo.flush()
    log("USUARIO_CREADO", f"usuario={user.id} rol={role.nombre}")
    repo.commit()

    row = user_row(user)
    row["password_temporal"] = password
    return ok(row, "Usuario creado", 201)


def users_update(user_id):
    user = repo.usuarios.get(user_id)
    if not user:
        return _not_found("Usuario")

    data = body()
    role = _role(text(data, "rol", user.rol.nombre))
    state = text(data, "estado", user.estado)
    email = text(data, "correo", user.email).lower()

    if not role:
        return fail("Rol no válido")
    if state not in ("Activo", "Inactivo") and state != user.estado:
        return fail("Estado no válido")
    if "@" not in email:
        return fail("Correo no válido")

    duplicate = repo.usuarios.email_en_uso_por_otro(email, user.id)
    if duplicate:
        return fail("Ya existe un usuario con ese correo", 409)

    error = _guard_admin_change(
        user,
        new_role=role.nombre if role.id != user.rol_id else None,
        new_state=state if state != user.estado else None
    )
    if error:
        return fail(error, 409)

    faculty, program, error = resolve_academic(text(data, "facultad"), text(data, "programa"))
    if error:
        return fail(error)

    user.nombre = text(data, "nombre", user.nombre) or user.nombre
    user.email = email
    user.rol_id = role.id
    user.estado = state
    if faculty:
        user.facultad_id = faculty.id
    if program:
        user.programa_id = program.id

    log("USUARIO_EDITADO", f"usuario={user.id} rol={role.nombre} estado={state}")
    repo.commit()
    return ok(user_row(user), "Usuario actualizado")


def users_state(user_id):
    user = repo.usuarios.get(user_id)
    if not user:
        return _not_found("Usuario")

    state = text(body(), "estado")
    if state not in ("Activo", "Inactivo") or user.estado in ("Pendiente", "Rechazado"):
        return fail("Estado no válido para este usuario")

    error = _guard_admin_change(user, new_state=state)
    if error:
        return fail(error, 409)

    user.estado = state
    log("USUARIO_ESTADO", f"usuario={user.id} estado={state}")
    repo.commit()
    return ok(user_row(user), "Estado actualizado")


def users_role(user_id):
    user = repo.usuarios.get(user_id)
    if not user:
        return _not_found("Usuario")

    role = _role(text(body(), "rol"))
    if not role:
        return fail("Rol no válido")
    if user.estado not in ("Activo", "Inactivo"):
        return fail("Solo se puede cambiar el rol de usuarios ya aprobados")

    error = _guard_admin_change(user, new_role=role.nombre)
    if error:
        return fail(error, 409)

    user.rol_id = role.id
    notify(user.id, "cuenta", f"Tu rol ahora es {role.nombre}")
    log("CAMBIO_ROL", f"usuario={user.id} rol={role.nombre}")
    repo.commit()
    return ok(user_row(user), "Rol actualizado")


def users_approve(user_id):
    user = repo.usuarios.get(user_id)
    if not user:
        return _not_found("Usuario")
    if user.estado not in ("Pendiente", "Rechazado"):
        return fail("La solicitud ya fue resuelta", 409)

    role = _role(text(body(), "rol", user.rol.nombre))
    if not role:
        return fail("Rol no válido")

    user.estado = "Activo"
    user.rol_id = role.id
    notify(user.id, "cuenta", "Tu cuenta fue aprobada. ¡Bienvenido a RIUL!")
    log("CUENTA_APROBADA", f"usuario={user.id} rol={role.nombre}")
    repo.commit()

    send_mail(user.email, "Cuenta RIUL aprobada",
              f"Hola {user.nombre}, tu cuenta fue aprobada. Ya puedes iniciar sesión.")
    return ok(user_row(user), "Cuenta aprobada")


def users_reject(user_id):
    user = repo.usuarios.get(user_id)
    if not user:
        return _not_found("Usuario")
    if user.estado != "Pendiente":
        return fail("La solicitud ya fue resuelta", 409)

    user.estado = "Rechazado"
    log("CUENTA_RECHAZADA", f"usuario={user.id}")
    repo.commit()

    send_mail(user.email, "Solicitud RIUL rechazada",
              f"Hola {user.nombre}, tu solicitud de registro no fue aprobada.")
    return ok(user_row(user), "Solicitud rechazada")


# ------------------------------------------------------------------
# Semilleros
# ------------------------------------------------------------------

def _lider(value):
    """Busca un docente líder por nombre o correo. Devuelve (usuario, error)."""
    if not value:
        return None, None

    user = repo.usuarios.docente_activo_por_nombre_o_correo(value)

    if not user:
        return None, "No existe un docente líder activo con ese nombre o correo"
    return user, None


def _semillero_by_name(name):
    return repo.semilleros.por_nombre(name)


def semilleros_list():
    return ok([semillero_row(s) for s in repo.semilleros.ordenados()])


def _save_semillero(sem, data):
    name = text(data, "nombre", sem.nombre or "")
    if not name:
        return "El nombre es obligatorio"

    if repo.semilleros.nombre_duplicado(name, sem.id):
        return "Ya existe un semillero con ese nombre"

    faculty, _, error = resolve_academic(text(data, "facultad"), "")
    if error:
        return error

    leader, error = _lider(text(data, "lider"))
    if error:
        return error

    sem.nombre = name
    sem.linea = text(data, "linea", sem.linea or "")
    sem.descripcion = text(data, "descripcion", sem.descripcion or "")
    if faculty:
        sem.facultad_id = faculty.id
    if "lider" in data:
        sem.docente_lider_id = leader.id if leader else None
    return None


def semilleros_create():
    sem = Semillero(estado="Activo")
    error = _save_semillero(sem, body())
    if error:
        return fail(error)

    repo.semilleros.add(sem)
    repo.flush()
    log("SEMILLERO_CREADO", f"semillero={sem.id}")
    repo.commit()
    return ok(semillero_row(sem), "Semillero creado", 201)


def semilleros_update(sem_id):
    sem = repo.semilleros.get(sem_id)
    if not sem:
        return _not_found("Semillero")

    error = _save_semillero(sem, body())
    if error:
        return fail(error)

    log("SEMILLERO_EDITADO", f"semillero={sem.id}")
    repo.commit()
    return ok(semillero_row(sem), "Semillero actualizado")


def semilleros_state(sem_id):
    sem = repo.semilleros.get(sem_id)
    if not sem:
        return _not_found("Semillero")

    state = text(body(), "estado")
    if state not in ("Activo", "Inactivo"):
        return fail("Estado no válido")

    sem.estado = state
    log("SEMILLERO_ESTADO", f"semillero={sem.id} estado={state}")
    repo.commit()
    return ok(semillero_row(sem), "Estado actualizado")


# ------------------------------------------------------------------
# Proyectos
# ------------------------------------------------------------------

PROYECTO_ESTADOS = ("Nuevo", "En curso", "Finalizado", "Suspendido")


def _save_proyecto(proyecto, data):
    name = text(data, "nombre", proyecto.nombre or "")
    sem = _semillero_by_name(text(data, "semillero")) if "semillero" in data else proyecto.semillero
    state = text(data, "estado", proyecto.estado or "Nuevo")

    if not name:
        return "El nombre es obligatorio"
    if not sem:
        return "El semillero indicado no existe"
    if state not in PROYECTO_ESTADOS:
        return "Estado no válido"

    proyecto.nombre = name
    proyecto.semillero_id = sem.id
    proyecto.estado = state
    proyecto.descripcion = text(data, "descripcion", proyecto.descripcion or "")
    if state == "Finalizado":
        proyecto.avance = 100
        proyecto.fecha_cierre = proyecto.fecha_cierre or utcnow().date()
    return None


def proyectos_list():
    return ok([proyecto_row(p) for p in repo.proyectos.recientes()])


def proyectos_create():
    proyecto = Proyecto(fecha_inicio=utcnow().date(), avance=0)
    error = _save_proyecto(proyecto, body())
    if error:
        return fail(error)

    repo.proyectos.add(proyecto)
    repo.flush()
    log("PROYECTO_CREADO", f"proyecto={proyecto.id}")
    repo.commit()
    return ok(proyecto_row(proyecto), "Proyecto creado", 201)


def proyectos_update(item_id):
    proyecto = repo.proyectos.get(item_id)
    if not proyecto:
        return _not_found("Proyecto")

    error = _save_proyecto(proyecto, body())
    if error:
        return fail(error)

    log("PROYECTO_EDITADO", f"proyecto={proyecto.id}")
    repo.commit()
    return ok(proyecto_row(proyecto), "Proyecto actualizado")


def proyectos_delete(item_id):
    proyecto = repo.proyectos.get(item_id)
    if not proyecto:
        return _not_found("Proyecto")

    borrar_proyecto(proyecto)
    log("PROYECTO_ELIMINADO", f"proyecto={item_id}")
    repo.commit()
    return ok(message="Proyecto eliminado")


# ------------------------------------------------------------------
# Eventos
# ------------------------------------------------------------------

def _save_evento(evento, data):
    name = text(data, "nombre", evento.nombre or "")
    when = parse_date(data.get("fecha")) if data.get("fecha") else evento.fecha
    modality = text(data, "modalidad", evento.modalidad or "Presencial")
    state = text(data, "estado", evento.estado or "Abierta")

    if not name:
        return "El nombre es obligatorio"
    if data.get("fecha") and not when:
        return "Fecha no válida (AAAA-MM-DD)"
    if modality not in ("Presencial", "Virtual", "Híbrida"):
        return "Modalidad no válida"
    if state not in ("Abierta", "Cerrada"):
        return "Estado no válido"

    sem = None
    if text(data, "semillero"):
        sem = _semillero_by_name(text(data, "semillero"))
        if not sem:
            return "El semillero indicado no existe"

    evento.nombre, evento.fecha, evento.modalidad, evento.estado = name, when, modality, state
    if "semillero" in data:
        evento.semillero_id = sem.id if sem else None
    if "descripcion" in data:
        evento.descripcion = text(data, "descripcion")
    return None


def eventos_list():
    return ok([evento_row(e) for e in repo.eventos.recientes()])


def eventos_create():
    evento = Evento()
    error = _save_evento(evento, body())
    if error:
        return fail(error)

    repo.eventos.add(evento)
    repo.flush()
    log("EVENTO_CREADO", f"evento={evento.id}")
    repo.commit()
    return ok(evento_row(evento), "Evento creado", 201)


def eventos_update(item_id):
    evento = repo.eventos.get(item_id)
    if not evento:
        return _not_found("Evento")

    error = _save_evento(evento, body())
    if error:
        return fail(error)

    log("EVENTO_EDITADO", f"evento={evento.id}")
    repo.commit()
    return ok(evento_row(evento), "Evento actualizado")


def eventos_delete(item_id):
    evento = repo.eventos.get(item_id)
    if not evento:
        return _not_found("Evento")

    borrar_evento(evento)
    log("EVENTO_ELIMINADO", f"evento={item_id}")
    repo.commit()
    return ok(message="Evento eliminado")


# ------------------------------------------------------------------
# Convocatorias (RF-32)
# ------------------------------------------------------------------

def _save_convocatoria(conv, data):
    title = text(data, "titulo", conv.titulo or "")
    state = text(data, "estado", conv.estado or "Abierta")
    closing = parse_date(data.get("cierre")) if data.get("cierre") else conv.cierre

    if not title:
        return "El título es obligatorio"
    if data.get("cierre") and not closing:
        return "Fecha de cierre no válida (AAAA-MM-DD)"
    if state not in ("Abierta", "Cerrada"):
        return "Estado no válido"

    conv.titulo, conv.estado, conv.cierre = title, state, closing
    if "descripcion" in data:
        conv.descripcion = text(data, "descripcion")
    return None


def convocatorias_list():
    return ok([convocatoria_row(c) for c in repo.convocatorias.recientes()])


def convocatorias_create():
    conv = Convocatoria(admin_id=current_user().id)
    error = _save_convocatoria(conv, body())
    if error:
        return fail(error)

    repo.convocatorias.add(conv)
    repo.flush()

    ids = repo.usuarios.ids_activos()
    notify_many(ids, "convocatoria", f"Nueva convocatoria: {conv.titulo}", "convocatoria", conv.id)
    log("CONVOCATORIA_CREADA", f"convocatoria={conv.id}")
    repo.commit()
    return ok(convocatoria_row(conv), "Convocatoria publicada", 201)


def convocatorias_update(item_id):
    conv = repo.convocatorias.get(item_id)
    if not conv:
        return _not_found("Convocatoria")

    error = _save_convocatoria(conv, body())
    if error:
        return fail(error)

    log("CONVOCATORIA_EDITADA", f"convocatoria={conv.id} estado={conv.estado}")
    repo.commit()
    return ok(convocatoria_row(conv), "Convocatoria actualizada")


def convocatorias_delete(item_id):
    conv = repo.convocatorias.get(item_id)
    if not conv:
        return _not_found("Convocatoria")

    borrar_convocatoria(conv)
    log("CONVOCATORIA_ELIMINADA", f"convocatoria={item_id}")
    repo.commit()
    return ok(message="Convocatoria eliminada")


# ------------------------------------------------------------------
# Publicaciones (moderación)
# ------------------------------------------------------------------

def publicaciones_list():
    return ok([publicacion_row(p) for p in repo.publicaciones.recientes()])


def publicaciones_state(item_id):
    pub = repo.publicaciones.get(item_id)
    if not pub:
        return _not_found("Publicación")

    state = text(body(), "estado")
    if state not in ("Publicada", "Oculta", "En revisión"):
        return fail("Estado no válido")

    if state == "Publicada" and pub.estado != "Publicada":
        publicar(pub, current_user())
    else:
        pub.estado = state
        log("PUBLICACION_ESTADO", f"publicacion={pub.id} estado={state}")

    repo.commit()
    return ok(publicacion_row(pub), "Publicación actualizada")


def publicaciones_delete(item_id):
    pub = repo.publicaciones.get(item_id)
    if not pub:
        return _not_found("Publicación")

    borrar_publicacion(pub)
    log("PUBLICACION_ELIMINADA", f"publicacion={item_id}")
    repo.commit()
    return ok(message="Publicación eliminada")


# ------------------------------------------------------------------
# Logros y productos (validación)
# ------------------------------------------------------------------

def logros_list():
    return ok([logro_row(l) for l in repo.logros.recientes()])


def logros_resolve(item_id):
    logro = repo.logros.get(item_id)
    if not logro:
        return _not_found("Logro")
    if logro.estado != "Pendiente":
        return fail("El logro ya fue validado", 409)

    data = body()
    state = text(data, "estado")
    if state not in ("Aprobado", "Rechazado"):
        return fail("Estado no válido")

    resolver_logro(logro, current_user(), state == "Aprobado", text(data, "observacion"))
    repo.commit()
    return ok(logro_row(logro), f"Logro {state.lower()}")


def productos_list():
    return ok([producto_row(p) for p in repo.productos.recientes()])


def productos_resolve(item_id):
    producto = repo.productos.get(item_id)
    if not producto:
        return _not_found("Producto")
    if producto.estado != "Pendiente":
        return fail("El producto ya fue validado", 409)

    state = text(body(), "estado")
    if state not in ("Aprobado", "Rechazado"):
        return fail("Estado no válido")

    me = current_user()
    producto.estado = state
    producto.validador_id = me.id
    sem = producto.semillero

    if state == "Aprobado":
        repo.historial_xp.registrar(
            semillero_id=sem.id, producto_id=producto.id, xp=XP_PRODUCTO,
            motivo=f"Producto validado: {producto.titulo}"[:200]
        )
        repo.flush()
        evaluar_insignias_semillero(sem)

    if sem.docente_lider_id:
        notify(sem.docente_lider_id, "logro",
               f"Tu producto «{producto.titulo}» fue {state.lower()}", "producto", producto.id)

    log("PRODUCTO_" + state.upper(), f"producto={producto.id}")
    repo.commit()
    return ok(producto_row(producto), f"Producto {state.lower()}")


# ------------------------------------------------------------------
# Facultades y programas (RF-19, RF-49)
# ------------------------------------------------------------------

def _facultad_row(f):
    return {
        "id": f.id,
        "nombre": f.nombre,
        "estado": "Activo" if f.activo else "Inactivo",
        "programas": repo.programas.contar_de(f.id)
    }


def _programa_row(p):
    return {
        "id": p.id,
        "nombre": p.nombre,
        "facultad": p.facultad.nombre,
        "estado": "Activo" if p.activo else "Inactivo"
    }


def facultades_list():
    return ok([_facultad_row(f) for f in repo.facultades.ordenadas()])


def facultades_create():
    name = text(body(), "nombre")
    if not name:
        return fail("El nombre es obligatorio")
    if repo.facultades.duplicada(name):
        return fail("La facultad ya existe", 409)

    faculty = Facultad(nombre=name)
    repo.facultades.add(faculty)
    repo.flush()
    log("FACULTAD_CREADA", f"facultad={faculty.id}")
    repo.commit()
    return ok(_facultad_row(faculty), "Facultad creada", 201)


def facultades_update(item_id):
    faculty = repo.facultades.get(item_id)
    if not faculty:
        return _not_found("Facultad")

    data = body()
    name = text(data, "nombre", faculty.nombre)
    if not name:
        return fail("El nombre es obligatorio")

    if repo.facultades.duplicada(name, faculty.id):
        return fail("La facultad ya existe", 409)

    faculty.nombre = name
    if "estado" in data:
        if data["estado"] not in ("Activo", "Inactivo"):
            return fail("Estado no válido")
        faculty.activo = data["estado"] == "Activo"

    log("FACULTAD_EDITADA", f"facultad={faculty.id}")
    repo.commit()
    return ok(_facultad_row(faculty), "Facultad actualizada")


def programas_list():
    return ok([_programa_row(p) for p in repo.programas.ordenados()])


def programas_save(item_id=None):
    data = body()
    program = repo.programas.get(item_id) if item_id else Programa()

    if item_id and not program:
        return _not_found("Programa")

    name = text(data, "nombre", program.nombre or "")
    if not name:
        return fail("El nombre es obligatorio")

    if "facultad" in data:
        faculty = repo.facultades.por_nombre(text(data, "facultad"))
        if not faculty:
            return fail("La facultad indicada no existe")
        program.facultad_id = faculty.id
    elif not item_id:
        return fail("La facultad es obligatoria")

    if repo.programas.duplicado(name, program.facultad_id, program.id):
        return fail("El programa ya existe en esa facultad", 409)

    program.nombre = name
    if "estado" in data:
        if data["estado"] not in ("Activo", "Inactivo"):
            return fail("Estado no válido")
        program.activo = data["estado"] == "Activo"

    if not item_id:
        repo.programas.add(program)
        repo.flush()

    log("PROGRAMA_GUARDADO", f"programa={program.id}")
    repo.commit()
    return ok(_programa_row(program), "Programa guardado", 200 if item_id else 201)


# ------------------------------------------------------------------
# Bitácora, indicadores, reportes y ranking institucional
# ------------------------------------------------------------------

def bitacora_list():
    rows = repo.bitacora.recientes(300)
    return ok([{
        "id": r.id,
        "fecha": r.fecha.strftime("%Y-%m-%d %H:%M"),
        "usuario": r.usuario.nombre if r.usuario else "Sistema",
        "accion": r.accion,
        "detalle": r.detalle or ""
    } for r in rows])


def indicadores_list():
    agrupar = request.args.get("agrupar", "facultad")
    if agrupar not in ("facultad", "programa", "semillero"):
        return fail("Agrupación no válida")

    desde = parse_date(request.args.get("desde"))
    hasta = parse_date(request.args.get("hasta"))
    return ok({
        "resumen": indicadores.resumen_global(),
        "filas": indicadores.por_grupo(agrupar, desde, hasta)
    })


def reportes(tipo):
    if tipo == "publicaciones":
        return csv_response(
            "publicaciones.csv",
            ["ID", "Título", "Tipo", "Semillero", "Autor", "Fecha", "Estado",
             "Reacciones", "Comentarios", "Compartidos", "Vistas"],
            [[p["id"], p["titulo"], p["tipo"], p["semillero"], p["autor"], p["fecha"], p["estado"],
              p["reacciones"], p["comentarios"], p["compartidos"], p["vistas"]]
             for p in map(publicacion_row, repo.publicaciones.por_id())]
        )

    if tipo == "logros":
        return csv_response(
            "logros.csv",
            ["ID", "Descripción", "Usuario", "Tipo", "XP", "Estado", "Fecha"],
            [[l["id"], l["descripcion"], l["usuario"], l["tipo"], l["xp"], l["estado"], l["fecha"]]
             for l in map(logro_row, repo.logros.por_id())]
        )

    if tipo == "proyectos":
        return csv_response(
            "proyectos.csv",
            ["ID", "Proyecto", "Semillero", "Estado", "Avance %", "Inicio"],
            [[p["id"], p["nombre"], p["semillero"], p["estado"], p["avance"], p["inicio"]]
             for p in map(proyecto_row, repo.proyectos.por_id())]
        )

    if tipo == "semilleros":
        return csv_response(
            "semilleros.csv",
            ["ID", "Semillero", "Facultad", "Línea", "Docente líder", "Integrantes", "XP", "Nivel", "Estado"],
            [[s["id"], s["nombre"], s["facultad"], s["linea"], s["lider"], s["integrantes"],
              s["xp"], s["nivel"], s["estado"]]
             for s in map(semillero_row, repo.semilleros.por_id())]
        )

    return fail("Tipo de reporte no válido", 404)


def get_config(key, default=""):
    return repo.configuracion.valor(key, default)


def ranking_config():
    return ok({"publicado": get_config("ranking_publicado", "1") == "1"})


def ranking_publish():
    published = bool(body().get("publicado"))
    repo.configuracion.establecer("ranking_publicado", "1" if published else "0")
    log("RANKING_PUBLICADO" if published else "RANKING_OCULTO", "")
    repo.commit()
    return ok({"publicado": published}, "Ranking publicado" if published else "Ranking oculto")
