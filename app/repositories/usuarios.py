"""Repositorios de usuarios, roles y códigos de recuperación."""

from sqlalchemy import func

from app.models import (
    CodigoRecuperacion, Rol, Usuario, ROL_ADMIN, ROL_DOCENTE, ROL_ESTUDIANTE, ROLES
)
from app.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository):
    model = Usuario

    def por_email(self, email):
        return Usuario.query.filter_by(email=email).first()

    def activo_por_email(self, email):
        return Usuario.query.filter_by(email=email, estado="Activo").first()

    def email_en_uso_por_otro(self, email, usuario_id):
        return Usuario.query.filter(
            Usuario.email == email, Usuario.id != usuario_id
        ).first()

    def recientes(self):
        return Usuario.query.order_by(Usuario.id.desc()).all()

    def contar_admins_activos(self):
        return Usuario.query.filter(
            Usuario.estado == "Activo", Usuario.rol.has(nombre=ROL_ADMIN)
        ).count()

    def contar_estudiantes_activos(self):
        return Usuario.query.filter(
            Usuario.estado == "Activo", Usuario.rol.has(nombre=ROL_ESTUDIANTE)
        ).count()

    def docente_activo_por_nombre_o_correo(self, valor):
        clave = valor.strip().lower()
        return Usuario.query.filter(
            Usuario.rol.has(nombre=ROL_DOCENTE),
            Usuario.estado == "Activo",
            (func.lower(Usuario.nombre) == clave) | (func.lower(Usuario.email) == clave)
        ).first()

    def ids_activos(self):
        return [u.id for u in Usuario.query.filter_by(estado="Activo")]

    def ids_admins_activos(self):
        return [
            u.id for u in Usuario.query.filter(
                Usuario.estado == "Activo", Usuario.rol.has(nombre=ROL_ADMIN)
            )
        ]

    def ids_activos_de_programa(self, programa_id):
        return [
            u.id for u in Usuario.query.filter_by(programa_id=programa_id, estado="Activo")
        ]

    def estudiantes_activos(self, facultad_id=None, programa_id=None):
        """Estudiantes activos, opcionalmente filtrados por facultad/programa."""
        query = Usuario.query.filter(
            Usuario.estado == "Activo", Usuario.rol.has(nombre=ROL_ESTUDIANTE)
        )
        if facultad_id:
            query = query.filter(Usuario.facultad_id == facultad_id)
        if programa_id:
            query = query.filter(Usuario.programa_id == programa_id)
        return query.all()


class RolRepository(BaseRepository):
    model = Rol

    def por_nombre(self, nombre):
        """Rol por nombre exacto, solo si es uno de los roles del sistema."""
        return Rol.query.filter_by(nombre=nombre).first() if nombre in ROLES else None

    def obtener(self, nombre):
        """Rol por nombre; lanza excepción si no existe (catálogo base)."""
        return Rol.query.filter_by(nombre=nombre).one()

    def hay_roles(self):
        return Rol.query.first() is not None


class CodigoRecuperacionRepository(BaseRepository):
    model = CodigoRecuperacion

    def invalidar_pendientes(self, usuario_id):
        CodigoRecuperacion.query.filter_by(
            usuario_id=usuario_id, usado=False
        ).update({"usado": True})

    def ultimo_pendiente(self, usuario_id):
        return (
            CodigoRecuperacion.query
            .filter_by(usuario_id=usuario_id, usado=False)
            .order_by(CodigoRecuperacion.id.desc())
            .first()
        )


usuarios = UsuarioRepository()
roles = RolRepository()
codigos_recuperacion = CodigoRecuperacionRepository()
