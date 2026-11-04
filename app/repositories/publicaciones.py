"""Repositorios de publicaciones, evidencias e interacción social."""

from sqlalchemy import func

from app.models import (
    CategoriaPublicacion, ComentarioPublicacion, CompartidoPublicacion,
    EvidenciaLogro, EvidenciaPublicacion, Publicacion, ReaccionPublicacion,
    VisualizacionPublicacion
)
from app.extencions import db
from app.repositories.base import BaseRepository


class PublicacionRepository(BaseRepository):
    model = Publicacion

    def recientes(self):
        return Publicacion.query.order_by(Publicacion.id.desc()).all()

    def por_id(self):
        return Publicacion.query.order_by(Publicacion.id).all()

    def de_semillero(self, semillero_id):
        return Publicacion.query.filter_by(
            semillero_id=semillero_id
        ).order_by(Publicacion.id.desc()).all()

    def publicas(self, semillero_id=None, termino="", limite=100):
        """Publicaciones con estado «Publicada», más recientes primero."""
        query = Publicacion.query.filter_by(estado="Publicada")

        if semillero_id:
            query = query.filter_by(semillero_id=semillero_id)

        termino = (termino or "").strip().lower()
        if termino:
            query = query.filter(func.lower(Publicacion.titulo).like(f"%{termino}%"))

        return query.order_by(Publicacion.fecha.desc()).limit(limite).all()

    def publicadas_de_semillero(self, semillero_id, limite=20):
        return (
            Publicacion.query.filter_by(semillero_id=semillero_id, estado="Publicada")
            .order_by(Publicacion.fecha.desc()).limit(limite).all()
        )

    def contar_publicadas(self, usuario_id=None, semillero_id=None):
        query = Publicacion.query.filter_by(estado="Publicada")
        if usuario_id is not None:
            query = query.filter_by(usuario_id=usuario_id)
        if semillero_id is not None:
            query = query.filter_by(semillero_id=semillero_id)
        return query.count()

    def contar_publicadas_en(self, semillero_ids=None, usuario_ids=None, desde=None, hasta=None):
        """
        Publicadas filtradas por semilleros y/o autores y periodo.
        Una lista vacía (no None) significa «ninguno» y devuelve 0.
        """
        query = Publicacion.query.filter(Publicacion.estado == "Publicada")

        if semillero_ids is not None:
            if not semillero_ids:
                return 0
            query = query.filter(Publicacion.semillero_id.in_(semillero_ids))

        if usuario_ids is not None:
            if not usuario_ids:
                return 0
            query = query.filter(Publicacion.usuario_id.in_(usuario_ids))

        if desde:
            query = query.filter(Publicacion.fecha >= desde)
        if hasta:
            query = query.filter(Publicacion.fecha <= hasta)

        return query.count()

    def eliminar(self, publicacion):
        """Borra la publicación con sus evidencias e interacciones."""
        for modelo in (EvidenciaPublicacion, ReaccionPublicacion, ComentarioPublicacion,
                       CompartidoPublicacion, VisualizacionPublicacion):
            modelo.query.filter_by(publicacion_id=publicacion.id).delete()
        self.delete(publicacion)


class CategoriaRepository(BaseRepository):
    model = CategoriaPublicacion

    def por_nombre(self, nombre):
        return CategoriaPublicacion.query.filter(
            func.lower(CategoriaPublicacion.nombre) == (nombre or "").lower()
        ).first()

    def ordenadas(self):
        return CategoriaPublicacion.query.order_by(CategoriaPublicacion.nombre).all()

    def ids_por_nombre(self):
        return {c.nombre: c.id for c in CategoriaPublicacion.query}


class EvidenciaRepository:
    """Evidencias (enlaces o archivos) de publicaciones y logros."""

    def de_publicacion(self, publicacion_id):
        return EvidenciaPublicacion.query.filter_by(publicacion_id=publicacion_id).all()

    def de_logro(self, logro_id):
        return EvidenciaLogro.query.filter_by(logro_id=logro_id).all()

    def agregar_a_publicacion(self, publicacion_id, tipo, url):
        evidencia = EvidenciaPublicacion(publicacion_id=publicacion_id, tipo=tipo, url=url)
        db.session.add(evidencia)
        return evidencia

    def agregar_a_logro(self, logro_id, tipo, url):
        evidencia = EvidenciaLogro(logro_id=logro_id, tipo=tipo, url=url)
        db.session.add(evidencia)
        return evidencia


class ReaccionRepository(BaseRepository):
    model = ReaccionPublicacion

    def de(self, publicacion_id, usuario_id):
        return ReaccionPublicacion.query.filter_by(
            publicacion_id=publicacion_id, usuario_id=usuario_id
        ).first()

    def contar_de(self, publicacion_id):
        return ReaccionPublicacion.query.filter_by(publicacion_id=publicacion_id).count()


class ComentarioRepository(BaseRepository):
    model = ComentarioPublicacion

    def de_publicacion(self, publicacion_id):
        return ComentarioPublicacion.query.filter_by(
            publicacion_id=publicacion_id
        ).order_by(ComentarioPublicacion.id).all()

    def contar_de(self, publicacion_id):
        return ComentarioPublicacion.query.filter_by(publicacion_id=publicacion_id).count()


class CompartidoRepository(BaseRepository):
    model = CompartidoPublicacion

    def contar_de(self, publicacion_id):
        return CompartidoPublicacion.query.filter_by(publicacion_id=publicacion_id).count()


class VisualizacionRepository(BaseRepository):
    model = VisualizacionPublicacion

    def contar_de(self, publicacion_id):
        return VisualizacionPublicacion.query.filter_by(publicacion_id=publicacion_id).count()


publicaciones = PublicacionRepository()
categorias = CategoriaRepository()
evidencias = EvidenciaRepository()
reacciones = ReaccionRepository()
comentarios = ComentarioRepository()
compartidos = CompartidoRepository()
visualizaciones = VisualizacionRepository()
