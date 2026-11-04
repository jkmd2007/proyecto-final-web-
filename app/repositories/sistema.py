"""Repositorios transversales: notificaciones, bitácora y configuración."""

from app.models import Bitacora, Configuracion, Notificacion
from app.repositories.base import BaseRepository


class NotificacionRepository(BaseRepository):
    model = Notificacion

    def recientes_de(self, usuario_id, limite=100):
        return (
            Notificacion.query.filter_by(usuario_id=usuario_id)
            .order_by(Notificacion.id.desc()).limit(limite).all()
        )

    def marcar_todas_leidas(self, usuario_id):
        Notificacion.query.filter_by(
            usuario_id=usuario_id, leida=False
        ).update({"leida": True})


class BitacoraRepository(BaseRepository):
    model = Bitacora

    def recientes(self, limite=300):
        return Bitacora.query.order_by(Bitacora.id.desc()).limit(limite).all()


class ConfiguracionRepository(BaseRepository):
    model = Configuracion

    def valor(self, clave, por_defecto=""):
        fila = self.get(clave)
        return fila.valor if fila else por_defecto

    def establecer(self, clave, valor):
        fila = self.get(clave) or Configuracion(clave=clave)
        fila.valor = valor
        self.add(fila)
        return fila


notificaciones = NotificacionRepository()
bitacora = BitacoraRepository()
configuracion = ConfiguracionRepository()
