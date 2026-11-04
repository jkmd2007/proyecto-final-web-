"""Repositorios de proyectos, avances y aportes."""

from app.models import AporteProyecto, AvanceProyecto, Proyecto, Semillero
from app.repositories.base import BaseRepository


class ProyectoRepository(BaseRepository):
    model = Proyecto

    def recientes(self):
        return Proyecto.query.order_by(Proyecto.id.desc()).all()

    def por_id(self):
        return Proyecto.query.order_by(Proyecto.id).all()

    def de_semillero(self, semillero_id):
        return Proyecto.query.filter_by(
            semillero_id=semillero_id
        ).order_by(Proyecto.id.desc()).all()

    def de_semilleros_activos(self):
        """Proyectos visibles al público: solo de semilleros activos."""
        return (
            Proyecto.query.join(Semillero)
            .filter(Semillero.estado == "Activo")
            .order_by(Proyecto.id.desc())
            .all()
        )

    def contar_total(self):
        return Proyecto.query.count()

    def contar_en_curso(self):
        return Proyecto.query.filter_by(estado="En curso").count()

    def contar_de_semillero(self, semillero_id):
        return Proyecto.query.filter_by(semillero_id=semillero_id).count()

    def contar_de_semilleros(self, semillero_ids):
        if not semillero_ids:
            return 0
        return Proyecto.query.filter(Proyecto.semillero_id.in_(semillero_ids)).count()

    def eliminar(self, proyecto):
        """Borra el proyecto junto con sus avances y aportes."""
        AvanceProyecto.query.filter_by(proyecto_id=proyecto.id).delete()
        AporteProyecto.query.filter_by(proyecto_id=proyecto.id).delete()
        self.delete(proyecto)


class AvanceRepository(BaseRepository):
    model = AvanceProyecto


class AporteRepository(BaseRepository):
    model = AporteProyecto

    def contar_de_usuario(self, usuario_id):
        return AporteProyecto.query.filter_by(usuario_id=usuario_id).count()


proyectos = ProyectoRepository()
avances = AvanceRepository()
aportes = AporteRepository()
