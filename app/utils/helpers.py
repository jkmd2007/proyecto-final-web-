"""Utilidades compartidas por las rutas del API."""

import csv
import io
from datetime import date
from functools import wraps

from flask import Response, g, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app import repositories as repo
from app.models import Bitacora, Notificacion


def ok(data=None, message=None, status=200):
    payload = {"data": data}
    if message:
        payload["message"] = message
    return jsonify(payload), status


def fail(message, status=400):
    return jsonify({"message": message}), status


def body():
    return request.get_json(silent=True) or {}


def text(data, key, default=""):
    value = data.get(key)
    return str(value).strip() if value is not None else default


def parse_date(value):
    """Devuelve date o None si el valor no es una fecha ISO válida."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def iso(value):
    return value.isoformat() if value else None


def current_user():
    return g.get("user")


def auth_required(*roles):
    """Exige JWT válido, cuenta activa y (opcionalmente) uno de los roles."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = repo.usuarios.get(int(get_jwt_identity()))

            if not user or user.estado != "Activo":
                return fail("Tu cuenta no está disponible", 401)

            if roles and user.rol.nombre not in roles:
                return fail("No tienes permisos para esta acción", 403)

            g.user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def optional_user():
    """Usuario autenticado si envía un token válido; None si es visitante."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
    except Exception:
        return None

    if not identity:
        return None

    user = repo.usuarios.get(int(identity))
    return user if user and user.estado == "Activo" else None


def log(accion, detalle="", usuario=None):
    """Registra una acción crítica en la bitácora (RNF-03). No hace commit."""
    user = usuario or g.get("user")
    repo.bitacora.add(Bitacora(
        usuario_id=user.id if user else None,
        accion=accion,
        detalle=str(detalle)[:500]
    ))


def notify(usuario_id, tipo, mensaje, ref_tipo=None, ref_id=None):
    repo.notificaciones.add(Notificacion(
        usuario_id=usuario_id,
        tipo=tipo,
        mensaje=mensaje[:300],
        referencia_tipo=ref_tipo,
        referencia_id=ref_id
    ))


def notify_many(usuario_ids, tipo, mensaje, ref_tipo=None, ref_id=None):
    for usuario_id in set(usuario_ids):
        notify(usuario_id, tipo, mensaje, ref_tipo, ref_id)


def csv_response(filename, headers, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)

    # BOM para que Excel respete las tildes
    return Response(
        "\ufeff" + buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
