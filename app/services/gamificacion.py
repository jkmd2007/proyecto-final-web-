"""XP, niveles (1-5 estrellas), insignias y ranking."""

from app import repositories as repo
from app.utils.helpers import log, notify
from app.models import utcnow

# XP mínimo acumulado para alcanzar cada nivel (1 a 5 estrellas)
LEVEL_THRESHOLDS = [0, 300, 800, 1500, 3000]

# XP que recibe el semillero al validarse uno de sus productos
XP_PRODUCTO = 200


def nivel_de(xp):
    nivel = 1
    for index, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp >= threshold:
            nivel = index + 1
    return nivel


def xp_siguiente(xp):
    for threshold in LEVEL_THRESHOLDS:
        if xp < threshold:
            return threshold
    return LEVEL_THRESHOLDS[-1]


def xp_total(usuario_id=None, semillero_id=None):
    return repo.historial_xp.total(usuario_id=usuario_id, semillero_id=semillero_id)


def semilleros_activos_de(usuario_id):
    """IDs de semilleros donde el usuario es integrante activo."""
    return [row.semillero_id for row in repo.integrantes.activos_de_usuario(usuario_id)]


def _metrica_usuario(usuario_id, criterio):
    if criterio == "logros":
        return repo.logros.contar_aprobados(usuario_id=usuario_id)
    if criterio == "xp":
        return xp_total(usuario_id=usuario_id)
    if criterio == "publicaciones":
        return repo.publicaciones.contar_publicadas(usuario_id=usuario_id)
    return 0


def _metrica_semillero(semillero_id, criterio):
    if criterio == "xp":
        return xp_total(semillero_id=semillero_id)
    if criterio == "proyectos":
        return repo.proyectos.contar_de_semillero(semillero_id)
    if criterio == "publicaciones":
        return repo.publicaciones.contar_publicadas(semillero_id=semillero_id)
    return 0


def evaluar_insignias_usuario(usuario):
    """Otorga las insignias de usuario cuyos criterios ya se cumplen (RF-42)."""
    tiene = repo.usuario_insignias.ids_de_usuario(usuario.id)

    for insignia in repo.insignias.de_destino("usuario"):
        if insignia.id in tiene:
            continue
        if _metrica_usuario(usuario.id, insignia.criterio) >= insignia.valor:
            repo.usuario_insignias.otorgar(usuario.id, insignia.id)
            notify(usuario.id, "insignia", f"Obtuviste la insignia «{insignia.nombre}»")


def evaluar_insignias_semillero(semillero):
    tiene = repo.semillero_insignias.ids_de_semillero(semillero.id)

    for insignia in repo.insignias.de_destino("semillero"):
        if insignia.id in tiene:
            continue
        if _metrica_semillero(semillero.id, insignia.criterio) >= insignia.valor:
            repo.semillero_insignias.otorgar(semillero.id, insignia.id)
            if semillero.docente_lider_id:
                notify(semillero.docente_lider_id, "insignia",
                       f"{semillero.nombre} obtuvo la insignia «{insignia.nombre}»")


def evaluar_todo(usuario):
    """Reevalúa insignias del usuario y de sus semilleros."""
    repo.flush()
    evaluar_insignias_usuario(usuario)

    for semillero_id in semilleros_activos_de(usuario.id):
        semillero = repo.semilleros.get(semillero_id)
        if semillero:
            evaluar_insignias_semillero(semillero)


def resolver_logro(logro, validador, aprobado, observacion=None):
    """
    Aprueba o rechaza un logro (RF-39). Si se aprueba asigna XP al usuario y a
    sus semilleros (RF-41), actualiza insignias (RF-42) y notifica (RF-47).
    Nivel y ranking se recalculan desde HistorialXP (RF-43 a RF-45).
    """
    logro.estado = "Aprobado" if aprobado else "Rechazado"
    logro.validador_id = validador.id
    logro.fecha_validacion = utcnow()
    logro.observacion = (observacion or "")[:300] or None

    if aprobado:
        xp = logro.tipo.xp
        repo.historial_xp.registrar(
            usuario_id=logro.usuario_id, logro_id=logro.id, xp=xp,
            motivo=f"Logro aprobado: {logro.descripcion}"[:200]
        )
        for semillero_id in semilleros_activos_de(logro.usuario_id):
            repo.historial_xp.registrar(
                semillero_id=semillero_id, logro_id=logro.id, xp=xp,
                motivo=f"Logro de integrante: {logro.descripcion}"[:200]
            )
        notify(logro.usuario_id, "logro", f"Tu logro «{logro.descripcion}» fue aprobado (+{xp} XP)",
               "logro", logro.id)
        log("LOGRO_APROBADO", f"logro={logro.id} usuario={logro.usuario_id} xp={xp}", validador)
        evaluar_todo(logro.usuario)
    else:
        notify(logro.usuario_id, "logro", f"Tu logro «{logro.descripcion}» fue rechazado",
               "logro", logro.id)
        log("LOGRO_RECHAZADO", f"logro={logro.id} usuario={logro.usuario_id}", validador)


def ranking_estudiantes(facultad_id=None, programa_id=None):

    totals = repo.historial_xp.totales_por_usuario()

    rows = []
    for user in repo.usuarios.estudiantes_activos(facultad_id, programa_id):
        xp = int(totals.get(user.id, 0) or 0)
        rows.append({
            "id": user.id,
            "nombre": user.nombre,
            "facultad": user.facultad.nombre if user.facultad else "",
            "programa": user.programa.nombre if user.programa else "",
            "xp": xp,
            "nivel": nivel_de(xp)
        })

    rows.sort(key=lambda row: (-row["xp"], row["nombre"]))

    for index, row in enumerate(rows, start=1):
        row["puesto"] = index

    return rows


def ranking_semilleros(facultad_id=None):

    totals = repo.historial_xp.totales_por_semillero()

    rows = []
    for sem in repo.semilleros.activos(facultad_id):
        xp = int(totals.get(sem.id, 0) or 0)
        rows.append({
            "id": sem.id,
            "nombre": sem.nombre,
            "facultad": sem.facultad.nombre if sem.facultad else "",
            "programa": "",
            "xp": xp,
            "nivel": nivel_de(xp)
        })

    rows.sort(key=lambda row: (-row["xp"], row["nombre"]))

    for index, row in enumerate(rows, start=1):
        row["puesto"] = index

    return rows
