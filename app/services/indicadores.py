"""Indicadores institucionales de producción investigativa (RF-50, RF-52, RF-54)."""

from app import repositories as repo
from app.services.gamificacion import xp_total


def _logros_de(user_ids, desde, hasta):
    return repo.logros.contar_aprobados_de(user_ids, desde, hasta)


def _publicaciones_de(semillero_ids=None, user_ids=None, desde=None, hasta=None):
    return repo.publicaciones.contar_publicadas_en(
        semillero_ids=semillero_ids, usuario_ids=user_ids, desde=desde, hasta=hasta
    )


def _fila(grupo, semillero_ids, desde, hasta):
    miembros = repo.integrantes.ids_usuarios_activos(semillero_ids)
    proyectos = repo.proyectos.contar_de_semilleros(semillero_ids)
    xp = sum(xp_total(semillero_id=sid) for sid in semillero_ids)

    return {
        "grupo": grupo,
        "semilleros": len(semillero_ids),
        "integrantes": len(miembros),
        "proyectos": proyectos,
        "publicaciones": _publicaciones_de(semillero_ids=semillero_ids, desde=desde, hasta=hasta),
        "logros": _logros_de(miembros, desde, hasta),
        "xp": xp
    }


def por_grupo(agrupar, desde=None, hasta=None):
    """agrupar: facultad | programa | semillero"""

    if agrupar == "programa":
        rows = []
        for programa in repo.programas.ordenados():
            ids = repo.usuarios.ids_activos_de_programa(programa.id)
            rows.append({
                "grupo": programa.nombre,
                "semilleros": 0,
                "integrantes": len(ids),
                "proyectos": 0,
                "publicaciones": _publicaciones_de(user_ids=ids, desde=desde, hasta=hasta),
                "logros": _logros_de(ids, desde, hasta),
                "xp": sum(xp_total(usuario_id=uid) for uid in ids)
            })
        return rows

    if agrupar == "semillero":
        return [
            _fila(sem.nombre, [sem.id], desde, hasta)
            for sem in repo.semilleros.ordenados()
        ]

    rows = []
    for facultad in repo.facultades.ordenadas():
        ids = repo.semilleros.ids_de_facultad(facultad.id)
        rows.append(_fila(facultad.nombre, ids, desde, hasta))
    return rows


def resumen_global():
    return {
        "semilleros": repo.semilleros.contar_activos(),
        "investigadores": repo.usuarios.contar_estudiantes_activos(),
        "proyectos": repo.proyectos.contar_total(),
        "proyectos_en_curso": repo.proyectos.contar_en_curso(),
        "publicaciones": repo.publicaciones.contar_publicadas(),
        "logros": repo.logros.contar_aprobados(),
        "eventos": repo.eventos.contar_total(),
        "xp_total": repo.historial_xp.total_global()
    }
