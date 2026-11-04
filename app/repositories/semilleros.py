"""Repositorios de semilleros, integrantes y seguidores."""

from sqlalchemy import func

from app.models import Facultad, Semillero, SemilleroIntegrante, SeguidorSemillero
from app.repositories.base import BaseRepository


class SemilleroRepository(BaseRepository):
    model = Semillero

    def ordenados(self):
        return Semillero.query.order_by(Semillero.nombre).all()

    def por_id(self):
        return Semillero.query.order_by(Semillero.id).all()

    def contar_activos(self):
        return Semillero.query.filter_by(estado="Activo").count()

    def activos(self, facultad_id=None):
        query = Semillero.query.filter_by(estado="Activo")
        if facultad_id:
            query = query.filter_by(facultad_id=facultad_id)
        return query.all()

    def por_nombre(self, nombre):
        return Semillero.query.filter(
            func.lower(Semillero.nombre) == (nombre or "").strip().lower()
        ).first()

    def nombre_duplicado(self, nombre, excluir_id=None):
        return Semillero.query.filter(
            func.lower(Semillero.nombre) == nombre.lower(),
            Semillero.id != (excluir_id or 0)
        ).first()

    def activo_de_lider(self, usuario_id):
        return Semillero.query.filter_by(
            docente_lider_id=usuario_id, estado="Activo"
        ).first()

    def ids_de_facultad(self, facultad_id):
        return [s.id for s in Semillero.query.filter_by(facultad_id=facultad_id)]

    def buscar_activos(self, termino="", facultad=""):
        """Búsqueda pública (RF-14) por texto y/o facultad."""
        query = Semillero.query.filter_by(estado="Activo")

        termino = (termino or "").strip().lower()
        if termino:
            like = f"%{termino}%"
            query = query.filter(
                func.lower(Semillero.nombre).like(like)
                | func.lower(Semillero.linea).like(like)
                | func.lower(Semillero.descripcion).like(like)
            )

        if facultad:
            query = query.join(Facultad, Semillero.facultad_id == Facultad.id).filter(
                func.lower(Facultad.nombre) == facultad.lower()
            )

        return query.order_by(Semillero.nombre).all()


class IntegranteRepository(BaseRepository):
    model = SemilleroIntegrante

    def activos_de_semillero(self, semillero_id):
        return SemilleroIntegrante.query.filter_by(
            semillero_id=semillero_id, estado="Activo"
        ).all()

    def activos_y_pendientes(self, semillero_id):
        return SemilleroIntegrante.query.filter(
            SemilleroIntegrante.semillero_id == semillero_id,
            SemilleroIntegrante.estado.in_(["Activo", "Pendiente"])
        ).order_by(SemilleroIntegrante.fecha_solicitud.desc()).all()

    def activos_de_usuario(self, usuario_id):
        return SemilleroIntegrante.query.filter_by(
            usuario_id=usuario_id, estado="Activo"
        ).all()

    def ids_usuarios_activos(self, semillero_ids):
        """IDs únicos de los integrantes activos de varios semilleros."""
        if not semillero_ids:
            return []
        filas = SemilleroIntegrante.query.filter(
            SemilleroIntegrante.semillero_id.in_(semillero_ids),
            SemilleroIntegrante.estado == "Activo"
        ).all()
        return list({fila.usuario_id for fila in filas})

    def contar_activos(self, semillero_id):
        return SemilleroIntegrante.query.filter_by(
            semillero_id=semillero_id, estado="Activo"
        ).count()


class SeguidorRepository(BaseRepository):
    model = SeguidorSemillero

    def ids_de_semillero(self, semillero_id):
        return [
            fila.usuario_id
            for fila in SeguidorSemillero.query.filter_by(semillero_id=semillero_id)
        ]


semilleros = SemilleroRepository()
integrantes = IntegranteRepository()
seguidores = SeguidorRepository()
