"""Controlador de auth: lógica de cada petición (MVC). Las URLs se declaran en app/routes/auth.py."""

import re
import secrets
from datetime import timedelta

from flask import current_app
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from app import repositories as repo
from app.models import (
    CodigoRecuperacion, Usuario, ROL_ESTUDIANTE, ROL_VISITANTE, utcnow
)
from app.schemas.serializers import user_public
from app.services.mailer import send_mail
from app.utils.helpers import (
    body, current_user, fail, log, notify, ok, text
)


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8


def _password_error(password):
    if len(password) < MIN_PASSWORD:
        return f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "La contraseña debe combinar letras y números"
    return None


def resolve_academic(faculty_name, program_name):
    """Devuelve (facultad, programa, error) a partir de nombres."""
    faculty = program = None

    if faculty_name:
        faculty = repo.facultades.activa_por_nombre(faculty_name)
        if not faculty:
            return None, None, "La facultad indicada no existe"

    if program_name:
        program = repo.programas.activo_por_nombre(
            program_name, faculty.id if faculty else None
        )
        if not program:
            return None, None, "El programa indicado no existe en la facultad seleccionada"
        faculty = faculty or program.facultad

    return faculty, program, None


def register():
    data = body()
    name = text(data, "name")
    email = text(data, "email").lower()
    password = data.get("password") or ""
    institutional = bool(data.get("institutional"))

    if not name or not email or not password:
        return fail("Nombre, correo y contraseña son obligatorios")

    if not EMAIL_RE.match(email):
        return fail("El correo no es válido")

    error = _password_error(password)
    if error:
        return fail(error)

    domain = current_app.config["INSTITUTIONAL_DOMAIN"]
    is_institutional_email = email.endswith("@" + domain)

    if institutional and not is_institutional_email:
        return fail(f"El correo institucional debe terminar en @{domain}")

    if repo.usuarios.por_email(email):
        return fail("Ya existe una cuenta con ese correo", 409)

    faculty, program, error = resolve_academic(text(data, "faculty"), text(data, "program"))
    if error:
        return fail(error)

    role_name = ROL_ESTUDIANTE if is_institutional_email else ROL_VISITANTE

    user = Usuario(
        nombre=name,
        email=email,
        tipo_cuenta="Institucional" if is_institutional_email else "Externa",
        estado="Pendiente",
        rol_id=repo.roles.obtener(role_name).id,
        facultad_id=faculty.id if faculty else None,
        programa_id=program.id if program else None
    )
    user.set_password(password)
    repo.usuarios.add(user)
    repo.flush()
    log("REGISTRO_SOLICITADO", f"email={email}", user)
    repo.commit()

    return ok(
        {"id": user.id},
        "Solicitud enviada. Un administrador validará tu cuenta y te notificaremos el resultado.",
        201
    )


def login():
    data = body()
    email = text(data, "email").lower()
    password = data.get("password") or ""

    user = repo.usuarios.por_email(email)

    if not user or not user.check_password(password):
        return fail("Correo o contraseña incorrectos", 401)

    if user.estado == "Pendiente":
        return fail("Tu cuenta está pendiente de aprobación por un administrador", 403)
    if user.estado == "Rechazado":
        return fail("Tu solicitud de registro fue rechazada", 403)
    if user.estado != "Activo":
        return fail("Tu cuenta está desactivada. Contacta al administrador", 403)

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.rol.nombre}
    )

    log("INICIO_SESION", f"usuario={user.id}", user)
    repo.commit()

    return ok({"access_token": token, "user": user_public(user)})


def logout():
    """El JWT es sin estado: el cliente descarta el token. Se deja traza."""
    log("CIERRE_SESION", f"usuario={current_user().id}")
    repo.commit()
    return ok(message="Sesión cerrada")


# ------------------------------------------------------------------
# Recuperación de acceso (RF-08): código de 6 dígitos con vencimiento
# ------------------------------------------------------------------

def recover():
    email = text(body(), "email").lower()
    user = repo.usuarios.por_email(email)

    response = {}

    if user and user.estado == "Activo":
        code = f"{secrets.randbelow(1000000):06d}"

        repo.codigos_recuperacion.invalidar_pendientes(user.id)
        repo.codigos_recuperacion.add(CodigoRecuperacion(
            usuario_id=user.id,
            codigo_hash=generate_password_hash(code),
            expira=utcnow() + timedelta(minutes=15)
        ))
        log("RECUPERACION_SOLICITADA", f"usuario={user.id}", user)
        repo.commit()

        send_mail(
            user.email,
            "Código de recuperación RIUL",
            f"Tu código de recuperación es {code}. Vence en 15 minutos."
        )

        if current_app.config["RESET_CODE_IN_RESPONSE"]:
            response["code"] = code  # solo para desarrollo, sin servidor de correo

    # Misma respuesta exista o no el correo (evita enumerar usuarios)
    return ok(response, "Si el correo está registrado, enviamos un código de recuperación.")


def reset():
    data = body()
    email = text(data, "email").lower()
    code = text(data, "code")
    password = data.get("password") or ""

    error = _password_error(password)
    if error:
        return fail(error)

    user = repo.usuarios.por_email(email)
    record = repo.codigos_recuperacion.ultimo_pendiente(user.id) if user else None

    if not record or record.expira < utcnow() or record.intentos >= 5:
        return fail("El código no es válido o ya venció", 400)

    if not check_password_hash(record.codigo_hash, code):
        record.intentos += 1
        repo.commit()
        return fail("El código no es válido o ya venció", 400)

    record.usado = True
    user.set_password(password)
    notify(user.id, "cuenta", "Tu contraseña fue actualizada")
    log("CONTRASENA_RESTABLECIDA", f"usuario={user.id}", user)
    repo.commit()

    return ok(message="Contraseña actualizada. Ya puedes iniciar sesión.")


# ------------------------------------------------------------------
# Perfil propio (RF-10)
# ------------------------------------------------------------------

def me():
    return ok(user_public(current_user()))


def update_me():
    user = current_user()
    data = body()

    name = text(data, "nombre") or user.nombre
    faculty, program, error = resolve_academic(
        text(data, "facultad"), text(data, "programa")
    )
    if error:
        return fail(error)

    user.nombre = name
    user.telefono = text(data, "telefono")[:30] or None
    user.biografia = text(data, "biografia") or None

    if faculty:
        user.facultad_id = faculty.id
    if program:
        user.programa_id = program.id

    log("PERFIL_ACTUALIZADO", f"usuario={user.id}")
    repo.commit()

    return ok(user_public(user), "Perfil actualizado")


def change_password():
    user = current_user()
    data = body()

    if not user.check_password(data.get("actual") or ""):
        return fail("La contraseña actual no es correcta", 400)

    error = _password_error(data.get("nueva") or "")
    if error:
        return fail(error)

    user.set_password(data["nueva"])
    log("CONTRASENA_CAMBIADA", f"usuario={user.id}")
    repo.commit()

    return ok(message="Contraseña actualizada")
