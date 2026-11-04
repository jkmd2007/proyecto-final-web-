"""Repositorios de tipos de logro, logros y productos de semillero."""

from sqlalchemy import func

from app.models import Logro, ProductoSemillero, TipoLogro
from app.repositories.base import BaseRepository


class TipoLogroRepository(BaseRepository):
    model = TipoLogro

    def por_nombre(self, nombre):
        return TipoLogro.query.filter(
            func.lower(TipoLogro.nombre) == (nombre or "").lower()
        ).first()

    def ordenados(self):
        return TipoLogro.query.order_by(TipoLogro.nombre).all()

    def ids_por_nombre(self):
        return {t.nombre: t.id for t in TipoLogro.query}


class LogroRepository(BaseRepository):
    model = Logro

    def recientes(self):
        return Logro.query.order_by(Logro.id.desc()).all()

    def por_id(self):
        return Logro.query.order_by(Logro.id).all()

    def de_usuario(self, usuario_id):
        return Logro.query.filter_by(usuario_id=usuario_id).order_by(Logro.id.desc()).all()

    def de_usuarios(self, usuario_ids):
        return Logro.query.filter(
            Logro.usuario_id.in_(usuario_ids)
        ).order_by(Logro.id.desc()).all()

    def aprobados_de_usuario(self, usuario_id):
        return (
            Logro.query.filter_by(usuario_id=usuario_id, estado="Aprobado")
            .order_by(Logro.fecha_validacion.desc()).all()
        )

    def aprobados_de_usuarios(self, usuario_ids, limite=10):
        return (
            Logro.query.filter(
                Logro.estado == "Aprobado", Logro.usuario_id.in_(usuario_ids or [0])
            )
            .order_by(Logro.fecha_validacion.desc()).limit(limite).all()
        )

    def contar_aprobados(self, usuario_id=None):
        query = Logro.query.filter_by(estado="Aprobado")
        if usuario_id is not None:
            query = query.filter_by(usuario_id=usuario_id)
        return query.count()

    def contar_aprobados_de(self, usuario_ids, desde=None, hasta=None):
        """Logros aprobados de un grupo de usuarios dentro de un periodo."""
        if not usuario_ids:
            return 0
        query = Logro.query.filter(
            Logro.estado == "Aprobado", Logro.usuario_id.in_(usuario_ids)
        )
        if desde:
            query = query.filter(Logro.fecha_validacion >= desde)
        if hasta:
            query = query.filter(Logro.fecha_validacion <= hasta)
        return query.count()


class ProductoRepository(BaseRepository):
    model = ProductoSemillero

    def recientes(self):
        return ProductoSemillero.query.order_by(ProductoSemillero.id.desc()).all()

    def de_semillero(self, semillero_id):
        return ProductoSemillero.query.filter_by(
            semillero_id=semillero_id
        ).order_by(ProductoSemillero.id.desc()).all()

    def aprobados_de_semillero(self, semillero_id):
        return ProductoSemillero.query.filter_by(
            semillero_id=semillero_id, estado="Aprobado"
        ).all()


tipos_logro = TipoLogroRepository()
logros = LogroRepository()
productos = ProductoRepository()
