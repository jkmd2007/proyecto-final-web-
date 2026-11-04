"""Datos iniciales: catálogos, administrador y (opcional) datos de demostración."""

from flask import current_app

from app import repositories as repo
from app.models import (
    AporteProyecto, CategoriaPublicacion, ComentarioPublicacion, Configuracion,
    Convocatoria, Evento, Facultad, Insignia, Logro, ParticipacionEvento,
    Programa, Proyecto, Publicacion, ReaccionPublicacion, Rol,
    SeguidorSemillero, Semillero, SemilleroIntegrante, TipoLogro, Usuario,
    ProductoSemillero, VisualizacionPublicacion, ROL_ADMIN, ROL_DOCENTE,
    ROL_ESTUDIANTE, ROLES, utcnow
)
from app.services.acciones import publicar
from app.services.gamificacion import evaluar_todo, resolver_logro
from datetime import timedelta

ESTRUCTURA = {
    "Ingeniería": ["Ingeniería de Sistemas", "Ingeniería Industrial"],
    "Derecho": ["Derecho"],
    "Ciencias de la Salud": ["Medicina", "Enfermería"],
    "Ciencias Económicas": ["Contaduría Pública", "Administración de Empresas"],
    "Ciencias Sociales": ["Psicología"]
}

TIPOS_LOGRO = {"Artículo": 300, "Ponencia": 150, "Producto": 200, "Patente": 500, "Evento": 80}
CATEGORIAS = ["Artículo", "Ponencia", "Producto", "Patente"]

INSIGNIAS = [
    ("Primer logro", "Tu primer logro fue aprobado", "usuario", "logros", 1),
    ("Investigador constante", "3 logros aprobados", "usuario", "logros", 3),
    ("Autor", "Tu primera publicación fue publicada", "usuario", "publicaciones", 1),
    ("Referente", "Alcanzaste 500 XP", "usuario", "xp", 500),
    ("Semillero activo", "El semillero registró su primer proyecto", "semillero", "proyectos", 1),
    ("Semillero productivo", "3 publicaciones publicadas", "semillero", "publicaciones", 3),
    ("Semillero destacado", "El semillero alcanzó 800 XP", "semillero", "xp", 800)
]

DEMO_PASSWORD = "Riul2026*"


def _user(name, email, role, faculty=None, program=None, estado="Activo", password=None, tipo=None):
    user = Usuario(
        nombre=name, email=email, estado=estado,
        tipo_cuenta=tipo or ("Institucional" if email.endswith("@unilibre.edu.co") else "Externa"),
        rol_id=repo.roles.obtener(role).id,
        facultad_id=repo.facultades.exacta(faculty).id if faculty else None,
        programa_id=repo.programas.primero_por_nombre(program).id if program else None
    )
    user.set_password(password or DEMO_PASSWORD)
    repo.usuarios.add(user)
    repo.flush()
    return user


def seed_base():
    if repo.roles.hay_roles():
        return

    for name in ROLES:
        repo.roles.add(Rol(nombre=name))

    for faculty, programs in ESTRUCTURA.items():
        record = Facultad(nombre=faculty)
        repo.facultades.add(record)
        repo.flush()
        for program in programs:
            repo.programas.add(Programa(nombre=program, facultad_id=record.id))

    for name in CATEGORIAS:
        repo.categorias.add(CategoriaPublicacion(nombre=name))

    for name, xp in TIPOS_LOGRO.items():
        repo.tipos_logro.add(TipoLogro(nombre=name, xp=xp))

    for name, description, target, criterion, value in INSIGNIAS:
        repo.insignias.add(Insignia(nombre=name, descripcion=description, destino=target,
                                    criterio=criterion, valor=value))

    repo.configuracion.add(Configuracion(clave="ranking_publicado", valor="1"))
    repo.flush()

    config = current_app.config
    _user(config["ADMIN_NAME"], config["ADMIN_EMAIL"], ROL_ADMIN, password=config["ADMIN_PASSWORD"])
    repo.commit()


def seed_demo():
    if not current_app.config["SEED_DEMO"] or repo.configuracion.get("demo_seeded"):
        return

    admin = repo.usuarios.por_email(current_app.config["ADMIN_EMAIL"])

    marcela = _user("Marcela Ortiz", "docente@unilibre.edu.co", ROL_DOCENTE,
                    "Ingeniería", "Ingeniería de Sistemas", password="Docente2026*")
    camilo = _user("Camilo Herrera", "camilo.herrera@unilibre.edu.co", ROL_DOCENTE,
                   "Ciencias de la Salud", "Medicina")

    elena = _user("Elena Ruiz", "estudiante@unilibre.edu.co", ROL_ESTUDIANTE,
                  "Ingeniería", "Ingeniería de Sistemas", password="Estudiante2026*")
    carlos = _user("Carlos Pérez", "carlos.perez@unilibre.edu.co", ROL_ESTUDIANTE,
                   "Ingeniería", "Ingeniería Industrial")
    ana = _user("Ana Gómez", "ana.gomez@unilibre.edu.co", ROL_ESTUDIANTE,
                "Ingeniería", "Ingeniería de Sistemas")
    luis = _user("Luis Mora", "luis.mora@unilibre.edu.co", ROL_ESTUDIANTE,
                 "Ciencias de la Salud", "Medicina")
    mateo = _user("Mateo Rojas", "mateo.rojas@unilibre.edu.co", ROL_ESTUDIANTE,
                  "Ingeniería", "Ingeniería Industrial")

    # Solicitudes de registro pendientes para probar la validación del administrador
    _user("Sofía Vega", "sofia.vega@unilibre.edu.co", ROL_ESTUDIANTE,
          "Ciencias de la Salud", "Enfermería", estado="Pendiente")
    _user("Valentina Cruz", "vcruz@correo.com", "Visitante",
          "Derecho", "Derecho", estado="Pendiente", tipo="Externa")

    datalab = Semillero(
        nombre="DataLab", linea="Ciencia de datos", estado="Activo",
        descripcion="Análisis de datos, visualización y proyectos aplicados a la investigación universitaria.",
        facultad_id=repo.facultades.exacta("Ingeniería").id,
        docente_lider_id=marcela.id
    )
    biolibre = Semillero(
        nombre="BioLibre", linea="Biodiversidad", estado="Activo",
        descripcion="Estudio de biodiversidad y salud pública en el Caribe colombiano.",
        facultad_id=repo.facultades.exacta("Ciencias de la Salud").id,
        docente_lider_id=camilo.id
    )
    repo.semilleros.add_all([datalab, biolibre])
    repo.flush()

    ahora = utcnow()
    for user, sem in ((elena, datalab), (carlos, datalab), (ana, datalab), (luis, biolibre)):
        repo.integrantes.add(SemilleroIntegrante(
            semillero_id=sem.id, usuario_id=user.id, estado="Activo", fecha_aprobacion=ahora
        ))
    repo.integrantes.add(SemilleroIntegrante(semillero_id=datalab.id, usuario_id=mateo.id, estado="Pendiente"))
    repo.seguidores.add(SeguidorSemillero(semillero_id=datalab.id, usuario_id=luis.id))

    p1 = Proyecto(semillero_id=datalab.id, nombre="Observatorio de datos académicos", estado="En curso",
                  avance=65, fecha_inicio=ahora.date() - timedelta(days=240),
                  descripcion="Tablero de indicadores académicos.")
    p2 = Proyecto(semillero_id=datalab.id, nombre="Clasificador de publicaciones RIUL", estado="Nuevo",
                  avance=10, fecha_inicio=ahora.date() - timedelta(days=45))
    p3 = Proyecto(semillero_id=biolibre.id, nombre="Biodiversidad del Caribe", estado="En curso",
                  avance=40, fecha_inicio=ahora.date() - timedelta(days=200))
    repo.proyectos.add_all([p1, p2, p3])
    repo.flush()
    repo.aportes.add(AporteProyecto(proyecto_id=p1.id, usuario_id=elena.id,
                                    descripcion="Limpieza y normalización del conjunto de datos."))

    categorias = repo.categorias.ids_por_nombre()
    pubs = [
        ("Modelo predictivo de deserción estudiantil", "Artículo", elena, datalab),
        ("Dashboard de indicadores de investigación", "Producto", carlos, datalab),
        ("Análisis de redes en semilleros Unilibre", "Ponencia", marcela, datalab),
        ("Inventario de especies del Caribe", "Artículo", camilo, biolibre)
    ]
    publicadas = []
    for title, category, author, sem in pubs:
        pub = Publicacion(titulo=title, usuario_id=author.id, semillero_id=sem.id,
                          categoria_id=categorias[category], contenido="Resumen disponible para la comunidad.")
        repo.publicaciones.add(pub)
        repo.flush()
        publicar(pub, admin)
        publicadas.append(pub)

    repo.publicaciones.add(Publicacion(titulo="Minería de texto en convocatorias internas", usuario_id=ana.id,
                                       semillero_id=datalab.id, categoria_id=categorias["Artículo"],
                                       estado="En revisión"))
    repo.flush()

    for user in (carlos, ana, luis):
        repo.reacciones.add(ReaccionPublicacion(publicacion_id=publicadas[0].id, usuario_id=user.id))
    repo.comentarios.add(ComentarioPublicacion(publicacion_id=publicadas[0].id, usuario_id=luis.id,
                                               contenido="Excelente trabajo, ¡felicitaciones!"))
    for _ in range(5):
        repo.visualizaciones.add(VisualizacionPublicacion(publicacion_id=publicadas[0].id))

    e1 = Evento(nombre="Encuentro nacional de semilleros", fecha=ahora.date() + timedelta(days=10),
                modalidad="Híbrida", semillero_id=datalab.id)
    e2 = Evento(nombre="Feria de investigación Unilibre", fecha=ahora.date() + timedelta(days=25),
                modalidad="Presencial", semillero_id=biolibre.id)
    repo.eventos.add_all([e1, e2])
    repo.flush()
    repo.participaciones.add(ParticipacionEvento(evento_id=e1.id, usuario_id=elena.id))

    repo.convocatorias.add_all([
        Convocatoria(titulo="Convocatoria interna de investigación", cierre=ahora.date() + timedelta(days=40),
                     descripcion="Financiación de proyectos de semilleros.", admin_id=admin.id),
        Convocatoria(titulo="Movilidad académica 2027", cierre=ahora.date() + timedelta(days=60), admin_id=admin.id),
        Convocatoria(titulo="Financiación de semilleros 2026-I", cierre=ahora.date() - timedelta(days=120),
                     estado="Cerrada", admin_id=admin.id)
    ])

    tipos = repo.tipos_logro.ids_por_nombre()
    aprobados = [
        (elena, "Primer artículo indexado", "Artículo"),
        (carlos, "Participación en feria de semilleros", "Evento"),
        (luis, "Ponencia en congreso regional", "Ponencia")
    ]
    for user, description, kind in aprobados:
        logro = Logro(usuario_id=user.id, tipo_logro_id=tipos[kind], descripcion=description)
        repo.logros.add(logro)
        repo.flush()
        resolver_logro(logro, marcela if user in (elena, carlos) else camilo, True)

    for user, description, kind in ((elena, "Ponencia nacional en ciencia de datos", "Ponencia"),
                                    (ana, "Participación en hackatón universitario", "Evento")):
        repo.logros.add(Logro(usuario_id=user.id, tipo_logro_id=tipos[kind], descripcion=description))

    repo.productos.add(ProductoSemillero(semillero_id=datalab.id, tipo="Software",
                                         titulo="Plataforma de analítica académica"))

    for user in (marcela, camilo, elena, carlos, ana, luis, mateo):
        evaluar_todo(user)

    repo.configuracion.add(Configuracion(clave="demo_seeded", valor="1"))
    repo.commit()
