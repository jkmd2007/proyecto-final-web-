"""
Capa de repositorios (acceso a datos) de RIUL.

Uso desde controladores y servicios::

    from app import repositories as repo

    usuario = repo.usuarios.por_email(email)
    repo.semilleros.add(semillero)
    repo.commit()
"""

from app.repositories.base import commit, flush, rollback  # noqa: F401
from app.repositories.academico import facultades, programas  # noqa: F401
from app.repositories.eventos import (  # noqa: F401
    convocatorias, eventos, participaciones, postulaciones
)
from app.repositories.gamificacion import (  # noqa: F401
    historial_xp, insignias, semillero_insignias, usuario_insignias
)
from app.repositories.logros import logros, productos, tipos_logro  # noqa: F401
from app.repositories.proyectos import aportes, avances, proyectos  # noqa: F401
from app.repositories.publicaciones import (  # noqa: F401
    categorias, comentarios, compartidos, evidencias, publicaciones, reacciones,
    visualizaciones
)
from app.repositories.semilleros import integrantes, seguidores, semilleros  # noqa: F401
from app.repositories.sistema import bitacora, configuracion, notificaciones  # noqa: F401
from app.repositories.usuarios import codigos_recuperacion, roles, usuarios  # noqa: F401
