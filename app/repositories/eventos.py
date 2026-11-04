"""Repositorios de eventos, convocatorias y sus participaciones."""

from app.models import Convocatoria, Evento, ParticipacionEvento, Postulacion
from app.repositories.base import BaseRepository


class EventoRepository(BaseRepository):
    model = Evento

    def recientes(self):
        return Evento.query.order_by(Evento.fecha.desc()).all()

    def de_semillero(self, semillero_id):
        return Evento.query.filter_by(
            semillero_id=semillero_id
        ).order_by(Evento.fecha.desc()).all()

    def contar_total(self):
        return Evento.query.count()

    def eliminar(self, evento):
        """Borra el evento junto con las participaciones registradas."""
        ParticipacionEvento.query.filter_by(evento_id=evento.id).delete()
        self.delete(evento)


class ParticipacionRepository(BaseRepository):
    model = ParticipacionEvento

    def contar_de_evento(self, evento_id):
        return ParticipacionEvento.query.filter_by(evento_id=evento_id).count()

    def de_usuario(self, usuario_id):
        return ParticipacionEvento.query.filter_by(usuario_id=usuario_id).all()


class ConvocatoriaRepository(BaseRepository):
    model = Convocatoria

    def recientes(self):
        return Convocatoria.query.order_by(Convocatoria.id.desc()).all()

    def eliminar(self, convocatoria):
        """Borra la convocatoria junto con sus postulaciones."""
        Postulacion.query.filter_by(convocatoria_id=convocatoria.id).delete()
        self.delete(convocatoria)


class PostulacionRepository(BaseRepository):
    model = Postulacion

    def de(self, convocatoria_id, usuario_id):
        return Postulacion.query.filter_by(
            convocatoria_id=convocatoria_id, usuario_id=usuario_id
        ).first()

    def contar_de_convocatoria(self, convocatoria_id):
        return Postulacion.query.filter_by(convocatoria_id=convocatoria_id).count()


eventos = EventoRepository()
participaciones = ParticipacionRepository()
convocatorias = ConvocatoriaRepository()
postulaciones = PostulacionRepository()
