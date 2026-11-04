"""Controlador de docente: lógica de cada petición (MVC). Las URLs se declaran en app/routes/docente.py."""

from functools import wraps

from app import repositories as repo
from app.controllers.auth_controller import resolve_academic
from app.models import (
    Evento, Logro, ProductoSemillero, Proyecto, AvanceProyecto, Publicacion,
    Semillero, SemilleroIntegrante, ROL_ESTUDIANTE, utcnow
)
from app.schemas.serializers import (
    evento_row, integrante_row, logro_row, producto_row, proyecto_row,
    publicacion_row, semillero_row
)
from app.services.acciones import (
    borrar_evento, borrar_publicacion, guardar_evidencias, publicar
)
from app.services.gamificacion import resolver_logro
from app.utils.helpers import (
    body, current_user, fail, log, notify, notify_many, ok, parse_date, text
)


def with_semillero(fn):
    """Inyecta el semillero activo que lidera el docente autenticado."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        sem = repo.semilleros.activo_de_lider(current_user().id)

        if not sem:
            return fail("Aún no tienes un semillero activo asignado. Contacta al administrador.", 404)

        return fn(sem, *args, **kwargs)

    return wrapper


# ------------------------------------------------------------------
# Semillero
# ------------------------------------------------------------------

def semillero_create():
    """RF-15: el docente líder crea su semillero (queda activo y a su cargo)."""
    me = current_user()

    if repo.semilleros.activo_de_lider(me.id):
        return fail("Ya lideras un semillero activo", 409)

    data = body()
    name = text(data, "nombre")
    description = text(data, "descripcion")
    line = text(data, "linea")

    if not name or not description or not line:
        return fail("Nombre, descripción y línea de investigación son obligatorios")
    if repo.semilleros.nombre_duplicado(name):
        return fail("Ya existe un semillero con ese nombre", 409)

    faculty_name = text(data, "facultad") or (me.facultad.nombre if me.facultad else "")
    if not faculty_name:
        return fail("Selecciona la facultad del semillero")

    faculty, _, error = resolve_academic(faculty_name, "")
    if error:
        return fail(error)

    sem = Semillero(
        nombre=name, descripcion=description, linea=line, estado="Activo",
        facultad_id=faculty.id, docente_lider_id=me.id
    )
    repo.semilleros.add(sem)
    repo.flush()

    notify_many(repo.usuarios.ids_admins_activos(), "semillero",
                f"{me.nombre} creó el semillero {sem.nombre}", "semillero", sem.id)
    log("SEMILLERO_CREADO", f"semillero={sem.id}")
    repo.commit()
    return ok(semillero_row(sem), "Semillero creado", 201)


@with_semillero
def semillero_get(sem):
    return ok(semillero_row(sem))


@with_semillero
def semillero_update(sem):
    """El docente solo edita descripción y línea; el resto lo administra RIUL."""
    data = body()
    description = text(data, "descripcion")
    line = text(data, "linea")

    if not description or not line:
        return fail("Descripción y línea de investigación son obligatorias")

    sem.descripcion, sem.linea = description, line
    log("SEMILLERO_EDITADO", f"semillero={sem.id}")
    repo.commit()
    return ok(semillero_row(sem), "Información del semillero actualizada")


# ------------------------------------------------------------------
# Integrantes
# ------------------------------------------------------------------

@with_semillero
def integrantes_list(sem):
    members = repo.integrantes.activos_y_pendientes(sem.id)
    return ok([integrante_row(m) for m in members])


@with_semillero
def integrantes_add(sem):
    email = text(body(), "correo").lower()
    user = repo.usuarios.activo_por_email(email)

    if not user or user.rol.nombre != ROL_ESTUDIANTE:
        return fail("No existe un estudiante investigador activo con ese correo", 404)

    member = repo.integrantes.get((sem.id, user.id))

    if member and member.estado == "Activo":
        return fail("El estudiante ya es integrante del semillero", 409)

    if not member:
        member = SemilleroIntegrante(semillero_id=sem.id, usuario_id=user.id)
        repo.integrantes.add(member)

    member.estado = "Activo"
    member.fecha_aprobacion = utcnow()
    notify(user.id, "semillero", f"Fuiste vinculado al semillero {sem.nombre}", "semillero", sem.id)
    log("INTEGRANTE_AGREGADO", f"semillero={sem.id} usuario={user.id}")
    repo.commit()
    return ok(integrante_row(member), "Integrante agregado", 201)


@with_semillero
def integrantes_resolve(sem, user_id):
    member = repo.integrantes.get((sem.id, user_id))
    if not member:
        return fail("El estudiante no está asociado a tu semillero", 404)

    state = text(body(), "estado")
    if state not in ("Activo", "Rechazado"):
        return fail("Estado no válido")

    member.estado = state
    if state == "Activo":
        member.fecha_aprobacion = utcnow()
        notify(user_id, "semillero", f"Tu solicitud de vinculación a {sem.nombre} fue aprobada",
               "semillero", sem.id)
    else:
        notify(user_id, "semillero", f"Tu solicitud de vinculación a {sem.nombre} fue rechazada",
               "semillero", sem.id)

    log("VINCULACION_" + state.upper(), f"semillero={sem.id} usuario={user_id}")
    repo.commit()
    return ok(integrante_row(member), "Solicitud resuelta")


@with_semillero
def integrantes_remove(sem, user_id):
    member = repo.integrantes.get((sem.id, user_id))
    if not member:
        return fail("El estudiante no está asociado a tu semillero", 404)

    repo.integrantes.delete(member)
    notify(user_id, "semillero", f"Fuiste removido del semillero {sem.nombre}", "semillero", sem.id)
    log("INTEGRANTE_REMOVIDO", f"semillero={sem.id} usuario={user_id}")
    repo.commit()
    return ok(message="Integrante removido")


# ------------------------------------------------------------------
# Proyectos (ciclo de vida completo, RF-23)
# ------------------------------------------------------------------

ESTADOS_PROYECTO = ("Nuevo", "En curso", "Finalizado", "Suspendido")


def _proyecto_of(sem, item_id):
    proyecto = repo.proyectos.get(item_id)
    return proyecto if proyecto and proyecto.semillero_id == sem.id else None


@with_semillero
def proyectos_list(sem):
    rows = repo.proyectos.de_semillero(sem.id)
    return ok([proyecto_row(p) for p in rows])


@with_semillero
def proyectos_create(sem):
    data = body()
    name = text(data, "nombre")
    state = text(data, "estado", "Nuevo")

    if not name:
        return fail("El nombre es obligatorio")
    if state not in ESTADOS_PROYECTO:
        return fail("Estado no válido")

    proyecto = Proyecto(
        semillero_id=sem.id, nombre=name, descripcion=text(data, "descripcion"),
        estado=state, avance=0, fecha_inicio=utcnow().date()
    )
    repo.proyectos.add(proyecto)
    repo.flush()
    log("PROYECTO_CREADO", f"proyecto={proyecto.id}")
    repo.commit()
    return ok(proyecto_row(proyecto), "Proyecto creado", 201)


@with_semillero
def proyectos_update(sem, item_id):
    proyecto = _proyecto_of(sem, item_id)
    if not proyecto:
        return fail("Proyecto no encontrado", 404)

    data = body()
    state = text(data, "estado", proyecto.estado)
    if state not in ESTADOS_PROYECTO:
        return fail("Estado no válido")

    proyecto.nombre = text(data, "nombre", proyecto.nombre) or proyecto.nombre
    proyecto.descripcion = text(data, "descripcion", proyecto.descripcion or "")
    proyecto.estado = state

    if "avance" in data:
        try:
            proyecto.avance = max(0, min(100, int(data["avance"])))
        except (TypeError, ValueError):
            return fail("El avance debe ser un número entre 0 y 100")

    if state == "Finalizado":
        proyecto.avance = 100
        proyecto.fecha_cierre = proyecto.fecha_cierre or utcnow().date()

    log("PROYECTO_EDITADO", f"proyecto={proyecto.id} estado={state}")
    repo.commit()
    return ok(proyecto_row(proyecto), "Proyecto actualizado")


@with_semillero
def proyectos_avance(sem, item_id):
    proyecto = _proyecto_of(sem, item_id)
    if not proyecto:
        return fail("Proyecto no encontrado", 404)

    data = body()
    try:
        percent = max(0, min(100, int(data.get("avance"))))
    except (TypeError, ValueError):
        return fail("El avance debe ser un número entre 0 y 100")

    repo.avances.add(AvanceProyecto(
        proyecto_id=proyecto.id, usuario_id=current_user().id,
        descripcion=text(data, "nota"), porcentaje=percent
    ))
    proyecto.avance = percent
    if proyecto.estado == "Nuevo":
        proyecto.estado = "En curso"

    log("PROYECTO_AVANCE", f"proyecto={proyecto.id} avance={percent}")
    repo.commit()
    return ok(proyecto_row(proyecto), "Avance publicado", 201)


# ------------------------------------------------------------------
# Publicaciones
# ------------------------------------------------------------------

def _categoria(name):
    return repo.categorias.por_nombre(name)


def _pub_of(sem, item_id):
    pub = repo.publicaciones.get(item_id)
    return pub if pub and pub.semillero_id == sem.id else None


@with_semillero
def publicaciones_list(sem):
    rows = repo.publicaciones.de_semillero(sem.id)
    return ok([publicacion_row(p) for p in rows])


@with_semillero
def publicaciones_create(sem):
    data = body()
    title = text(data, "titulo")
    category = _categoria(text(data, "tipo"))

    if not title:
        return fail("El título es obligatorio")
    if not category:
        return fail("Tipo de publicación no válido")

    pub = Publicacion(
        titulo=title, contenido=text(data, "contenido"), estado="En revisión",
        usuario_id=current_user().id, semillero_id=sem.id, categoria_id=category.id
    )
    repo.publicaciones.add(pub)
    repo.flush()

    error = guardar_evidencias("publicacion", pub.id, data)
    if error:
        repo.rollback()
        return fail(error)

    log("PUBLICACION_CREADA", f"publicacion={pub.id}")
    repo.commit()
    return ok(publicacion_row(pub), "Publicación creada", 201)


@with_semillero
def publicaciones_update(sem, item_id):
    pub = _pub_of(sem, item_id)
    if not pub:
        return fail("Publicación no encontrada", 404)

    data = body()
    category = _categoria(text(data, "tipo", pub.categoria.nombre))
    if not category:
        return fail("Tipo de publicación no válido")

    pub.titulo = text(data, "titulo", pub.titulo) or pub.titulo
    pub.categoria_id = category.id

    error = guardar_evidencias("publicacion", pub.id, data)
    if error:
        repo.rollback()
        return fail(error)

    log("PUBLICACION_EDITADA", f"publicacion={pub.id}")
    repo.commit()
    return ok(publicacion_row(pub), "Publicación actualizada")


@with_semillero
def publicaciones_state(sem, item_id):
    pub = _pub_of(sem, item_id)
    if not pub:
        return fail("Publicación no encontrada", 404)

    state = text(body(), "estado")
    if state not in ("Publicada", "En revisión", "Oculta"):
        return fail("Estado no válido")

    if state == "Publicada" and pub.estado != "Publicada":
        publicar(pub, current_user())
    else:
        pub.estado = state
        log("PUBLICACION_ESTADO", f"publicacion={pub.id} estado={state}")

    repo.commit()
    return ok(publicacion_row(pub), "Publicación actualizada")


@with_semillero
def publicaciones_delete(sem, item_id):
    pub = _pub_of(sem, item_id)
    if not pub:
        return fail("Publicación no encontrada", 404)

    borrar_publicacion(pub)
    log("PUBLICACION_ELIMINADA", f"publicacion={item_id}")
    repo.commit()
    return ok(message="Publicación eliminada")


# ------------------------------------------------------------------
# Eventos (RF-31)
# ------------------------------------------------------------------

def _evento_of(sem, item_id):
    evento = repo.eventos.get(item_id)
    return evento if evento and evento.semillero_id == sem.id else None


@with_semillero
def eventos_list(sem):
    rows = repo.eventos.de_semillero(sem.id)
    return ok([evento_row(e) for e in rows])


def _fill_evento(evento, data):
    name = text(data, "nombre", evento.nombre or "")
    modality = text(data, "modalidad", evento.modalidad or "Presencial")
    when = parse_date(data.get("fecha")) if data.get("fecha") else evento.fecha

    if not name:
        return "El nombre es obligatorio"
    if data.get("fecha") and not when:
        return "Fecha no válida (AAAA-MM-DD)"
    if modality not in ("Presencial", "Virtual", "Híbrida"):
        return "Modalidad no válida"

    evento.nombre, evento.modalidad, evento.fecha = name, modality, when
    return None


@with_semillero
def eventos_create(sem):
    evento = Evento(semillero_id=sem.id, estado="Abierta")
    error = _fill_evento(evento, body())
    if error:
        return fail(error)

    repo.eventos.add(evento)
    repo.flush()
    log("EVENTO_REGISTRADO", f"evento={evento.id}")
    repo.commit()
    return ok(evento_row(evento), "Evento registrado", 201)


@with_semillero
def eventos_update(sem, item_id):
    evento = _evento_of(sem, item_id)
    if not evento:
        return fail("Evento no encontrado", 404)

    error = _fill_evento(evento, body())
    if error:
        return fail(error)

    log("EVENTO_EDITADO", f"evento={evento.id}")
    repo.commit()
    return ok(evento_row(evento), "Evento actualizado")


@with_semillero
def eventos_delete(sem, item_id):
    evento = _evento_of(sem, item_id)
    if not evento:
        return fail("Evento no encontrado", 404)

    borrar_evento(evento)
    log("EVENTO_ELIMINADO", f"evento={item_id}")
    repo.commit()
    return ok(message="Evento eliminado")


# ------------------------------------------------------------------
# Logros (propios y de los integrantes)
# ------------------------------------------------------------------

def _member_ids(sem):
    return [row.usuario_id for row in repo.integrantes.activos_de_semillero(sem.id)]


@with_semillero
def logros_list(sem):
    ids = _member_ids(sem) + [current_user().id]
    rows = repo.logros.de_usuarios(ids)
    return ok([logro_row(l) for l in rows])


@with_semillero
def logros_create(sem):
    """El logro del propio docente lo valida un administrador (RF-38)."""
    data = body()
    description = text(data, "descripcion")
    kind = repo.tipos_logro.por_nombre(text(data, "tipo"))

    if not description:
        return fail("La descripción es obligatoria")
    if not kind:
        return fail("Tipo de logro no válido")
    if not (data.get("evidencia") or data.get("archivo")):
        return fail("Adjunta una evidencia (enlace o archivo) antes de enviar el logro")

    logro = Logro(usuario_id=current_user().id, tipo_logro_id=kind.id, descripcion=description[:300])
    repo.logros.add(logro)
    repo.flush()

    error = guardar_evidencias("logro", logro.id, data)
    if error:
        repo.rollback()
        return fail(error)

    log("LOGRO_REGISTRADO", f"logro={logro.id}")
    repo.commit()
    return ok(logro_row(logro), "Logro enviado a validación", 201)


@with_semillero
def logros_resolve(sem, item_id):
    logro = repo.logros.get(item_id)
    me = current_user()

    if not logro or logro.usuario_id not in _member_ids(sem):
        return fail("Solo puedes validar logros de integrantes de tu semillero", 404)
    if logro.estado != "Pendiente":
        return fail("El logro ya fue validado", 409)

    data = body()
    state = text(data, "estado")
    if state not in ("Aprobado", "Rechazado"):
        return fail("Estado no válido")

    resolver_logro(logro, me, state == "Aprobado", text(data, "observacion"))
    repo.commit()
    return ok(logro_row(logro), f"Logro {state.lower()}")


# ------------------------------------------------------------------
# Productos del semillero (RF-40)
# ------------------------------------------------------------------

@with_semillero
def productos_list(sem):
    rows = repo.productos.de_semillero(sem.id)
    return ok([producto_row(p) for p in rows])


@with_semillero
def productos_create(sem):
    data = body()
    title = text(data, "titulo")
    kind = text(data, "tipo")

    if not title or kind not in ("Artículo", "Patente", "Ponencia", "Software", "Otro"):
        return fail("Título y tipo de producto válidos son obligatorios")

    producto = ProductoSemillero(
        semillero_id=sem.id, tipo=kind, titulo=title, descripcion=text(data, "descripcion")
    )
    repo.productos.add(producto)
    repo.flush()
    log("PRODUCTO_REGISTRADO", f"producto={producto.id}")
    repo.commit()
    return ok(producto_row(producto), "Producto enviado a validación", 201)


@with_semillero
def productos_delete(sem, item_id):
    producto = repo.productos.get(item_id)

    if not producto or producto.semillero_id != sem.id:
        return fail("Producto no encontrado", 404)
    if producto.estado != "Pendiente":
        return fail("Solo se pueden eliminar productos pendientes", 409)

    repo.productos.delete(producto)
    repo.commit()
    return ok(message="Producto eliminado")
