"""Repositorios de la estructura académica: facultades y programas."""

from sqlalchemy import func

from app.models import Facultad, Programa
from app.repositories.base import BaseRepository


class FacultadRepository(BaseRepository):
    model = Facultad

    def exacta(self, nombre):
        """Facultad por nombre exacto (catálogo/seed); falla si no existe."""
        return Facultad.query.filter_by(nombre=nombre).one()

    def por_nombre(self, nombre):
        return Facultad.query.filter(func.lower(Facultad.nombre) == nombre.lower()).first()

    def activa_por_nombre(self, nombre):
        return Facultad.query.filter(
            func.lower(Facultad.nombre) == nombre.lower(), Facultad.activo.is_(True)
        ).first()

    def duplicada(self, nombre, excluir_id=None):
        query = Facultad.query.filter(func.lower(Facultad.nombre) == nombre.lower())
        if excluir_id is not None:
            query = query.filter(Facultad.id != excluir_id)
        return query.first()

    def ordenadas(self):
        return Facultad.query.order_by(Facultad.nombre).all()

    def activas(self):
        return Facultad.query.filter_by(activo=True).order_by(Facultad.nombre).all()


class ProgramaRepository(BaseRepository):
    model = Programa

    def primero_por_nombre(self, nombre):
        """Programa por nombre exacto (seed); None si no existe."""
        return Programa.query.filter_by(nombre=nombre).first()

    def por_nombre(self, nombre):
        return Programa.query.filter(func.lower(Programa.nombre) == nombre.lower()).first()

    def activo_por_nombre(self, nombre, facultad_id=None):
        query = Programa.query.filter(
            func.lower(Programa.nombre) == nombre.lower(), Programa.activo.is_(True)
        )
        if facultad_id:
            query = query.filter(Programa.facultad_id == facultad_id)
        return query.first()

    def duplicado(self, nombre, facultad_id, excluir_id=None):
        return Programa.query.filter(
            func.lower(Programa.nombre) == nombre.lower(),
            Programa.facultad_id == facultad_id,
            Programa.id != (excluir_id or 0)
        ).first()

    def ordenados(self):
        return Programa.query.order_by(Programa.nombre).all()

    def activos_de(self, facultad_id):
        return Programa.query.filter_by(
            facultad_id=facultad_id, activo=True
        ).order_by(Programa.nombre).all()

    def contar_de(self, facultad_id):
        return Programa.query.filter_by(facultad_id=facultad_id).count()


facultades = FacultadRepository()
programas = ProgramaRepository()
