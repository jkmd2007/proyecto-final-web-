"""
Base de la capa de repositorios (acceso a datos).

MVC en RIUL:  routes -> controllers -> services / repositories -> models.
Los repositorios son los únicos que consultan la base de datos; los
controladores y servicios piden datos con métodos de intención clara
(p. ej. ``repo.usuarios.por_email``) y deciden cuándo confirmar la
transacción con ``commit()`` (unidad de trabajo).
"""

from app.extencions import db


# ------------------------------------------------------------------
# Unidad de trabajo (transacción de la petición)
# ------------------------------------------------------------------

def commit():
    db.session.commit()


def flush():
    db.session.flush()


def rollback():
    db.session.rollback()


class BaseRepository:
    """Operaciones comunes. Cada repositorio concreto fija ``model``."""

    model = None

    def get(self, ident):
        """Busca por clave primaria (o tupla para claves compuestas)."""
        return db.session.get(self.model, ident)

    def add(self, entity):
        db.session.add(entity)
        return entity

    def add_all(self, entities):
        db.session.add_all(entities)
        return entities

    def delete(self, entity):
        db.session.delete(entity)

    def todos(self):
        return self.model.query.all()

    def contar(self, **filtros):
        return self.model.query.filter_by(**filtros).count()

    def buscar(self, **filtros):
        """Primer registro que cumpla los filtros de igualdad, o None."""
        return self.model.query.filter_by(**filtros).first()

    def donde(self, **filtros):
        """Todos los registros que cumplan los filtros de igualdad."""
        return self.model.query.filter_by(**filtros).all()
