"""Repositorios de gamificación: libro de XP e insignias."""

from sqlalchemy import func

from app.extencions import db
from app.models import HistorialXP, Insignia, SemilleroInsignia, UsuarioInsignia
from app.repositories.base import BaseRepository


class HistorialXPRepository(BaseRepository):
    """El libro de XP es la fuente de verdad de puntaje, nivel y ranking."""

    model = HistorialXP

    def total(self, usuario_id=None, semillero_id=None):
        query = db.session.query(func.coalesce(func.sum(HistorialXP.xp), 0))

        if usuario_id is not None:
            query = query.filter(HistorialXP.usuario_id == usuario_id)
        if semillero_id is not None:
            query = query.filter(HistorialXP.semillero_id == semillero_id)

        return int(query.scalar() or 0)

    def total_global(self):
        return int(
            db.session.query(func.coalesce(func.sum(HistorialXP.xp), 0)).scalar() or 0
        )

    def totales_por_usuario(self):
        """{usuario_id: xp acumulado}"""
        return dict(
            db.session.query(HistorialXP.usuario_id, func.sum(HistorialXP.xp))
            .filter(HistorialXP.usuario_id.isnot(None))
            .group_by(HistorialXP.usuario_id).all()
        )

    def totales_por_semillero(self):
        """{semillero_id: xp acumulado}"""
        return dict(
            db.session.query(HistorialXP.semillero_id, func.sum(HistorialXP.xp))
            .filter(HistorialXP.semillero_id.isnot(None))
            .group_by(HistorialXP.semillero_id).all()
        )

    def registrar(self, **campos):
        return self.add(HistorialXP(**campos))


class InsigniaRepository(BaseRepository):
    model = Insignia

    def de_destino(self, destino):
        return Insignia.query.filter_by(destino=destino).all()


class UsuarioInsigniaRepository(BaseRepository):
    model = UsuarioInsignia

    def ids_de_usuario(self, usuario_id):
        return {
            fila.insignia_id
            for fila in UsuarioInsignia.query.filter_by(usuario_id=usuario_id)
        }

    def de_usuario(self, usuario_id):
        return UsuarioInsignia.query.filter_by(usuario_id=usuario_id).all()

    def otorgar(self, usuario_id, insignia_id):
        return self.add(UsuarioInsignia(usuario_id=usuario_id, insignia_id=insignia_id))


class SemilleroInsigniaRepository(BaseRepository):
    model = SemilleroInsignia

    def ids_de_semillero(self, semillero_id):
        return {
            fila.insignia_id
            for fila in SemilleroInsignia.query.filter_by(semillero_id=semillero_id)
        }

    def otorgar(self, semillero_id, insignia_id):
        return self.add(SemilleroInsignia(semillero_id=semillero_id, insignia_id=insignia_id))


historial_xp = HistorialXPRepository()
insignias = InsigniaRepository()
usuario_insignias = UsuarioInsigniaRepository()
semillero_insignias = SemilleroInsigniaRepository()
