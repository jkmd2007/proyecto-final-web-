"""
Modelo de datos de RIUL (normalizado hasta 3FN).

Notas de diseño:
- XP, nivel y ranking NO se guardan como columnas: se calculan desde
  HistorialXP (ver services/gamificacion.py).
- Las estadísticas de publicaciones se calculan con COUNT sobre
  reacciones, comentarios, compartidos y visualizaciones.
"""

from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extencions import db

ROL_ADMIN = "Administrador"
ROL_DOCENTE = "Docente Líder"
ROL_ESTUDIANTE = "Estudiante Investigador"
ROL_VISITANTE = "Visitante"
ROLES = [ROL_ADMIN, ROL_DOCENTE, ROL_ESTUDIANTE, ROL_VISITANTE]


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ------------------------------------------------------------------
# Usuarios, roles y estructura académica
# ------------------------------------------------------------------

class Rol(db.Model):
    __tablename__ = "rol"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(40), unique=True, nullable=False)


class Facultad(db.Model):
    __tablename__ = "facultad"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)


class Programa(db.Model):
    __tablename__ = "programa"
    __table_args__ = (db.UniqueConstraint("nombre", "facultad_id"),)

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    facultad_id = db.Column(db.Integer, db.ForeignKey("facultad.id"), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    facultad = db.relationship("Facultad")


class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    tipo_cuenta = db.Column(db.String(20), nullable=False, default="Institucional")
    # Pendiente | Activo | Inactivo | Rechazado
    estado = db.Column(db.String(20), nullable=False, default="Pendiente")
    fecha_registro = db.Column(db.DateTime, nullable=False, default=utcnow)
    telefono = db.Column(db.String(30))
    biografia = db.Column(db.Text)
    rol_id = db.Column(db.Integer, db.ForeignKey("rol.id"), nullable=False)
    facultad_id = db.Column(db.Integer, db.ForeignKey("facultad.id"))
    programa_id = db.Column(db.Integer, db.ForeignKey("programa.id"))

    rol = db.relationship("Rol")
    facultad = db.relationship("Facultad")
    programa = db.relationship("Programa")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def es_admin(self):
        return self.rol.nombre == ROL_ADMIN

    @property
    def es_docente(self):
        return self.rol.nombre == ROL_DOCENTE


class CodigoRecuperacion(db.Model):
    __tablename__ = "codigo_recuperacion"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    codigo_hash = db.Column(db.String(255), nullable=False)
    expira = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, nullable=False, default=False)
    intentos = db.Column(db.Integer, nullable=False, default=0)


# ------------------------------------------------------------------
# Semilleros y proyectos
# ------------------------------------------------------------------

class Semillero(db.Model):
    __tablename__ = "semillero"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    linea = db.Column(db.String(150))
    estado = db.Column(db.String(20), nullable=False, default="Activo")
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=utcnow)
    facultad_id = db.Column(db.Integer, db.ForeignKey("facultad.id"))
    docente_lider_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))

    facultad = db.relationship("Facultad")
    lider = db.relationship("Usuario", foreign_keys=[docente_lider_id])


class SemilleroIntegrante(db.Model):
    __tablename__ = "semillero_integrante"

    semillero_id = db.Column(db.Integer, db.ForeignKey("semillero.id"), primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    # Pendiente | Activo | Rechazado
    estado = db.Column(db.String(20), nullable=False, default="Pendiente")
    fecha_solicitud = db.Column(db.DateTime, nullable=False, default=utcnow)
    fecha_aprobacion = db.Column(db.DateTime)

    semillero = db.relationship("Semillero")
    usuario = db.relationship("Usuario")


class SeguidorSemillero(db.Model):
    __tablename__ = "seguidor_semillero"

    semillero_id = db.Column(db.Integer, db.ForeignKey("semillero.id"), primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)


class Proyecto(db.Model):
    __tablename__ = "proyecto"

    id = db.Column(db.Integer, primary_key=True)
    semillero_id = db.Column(db.Integer, db.ForeignKey("semillero.id"), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    # Nuevo | En curso | Finalizado | Suspendido
    estado = db.Column(db.String(20), nullable=False, default="Nuevo")
    avance = db.Column(db.Integer, nullable=False, default=0)
    fecha_inicio = db.Column(db.Date)
    fecha_cierre = db.Column(db.Date)

    semillero = db.relationship("Semillero")


class AvanceProyecto(db.Model):
    __tablename__ = "avance_proyecto"

    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey("proyecto.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    descripcion = db.Column(db.Text)
    porcentaje = db.Column(db.Integer, nullable=False, default=0)
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)


class AporteProyecto(db.Model):
    __tablename__ = "aporte_proyecto"

    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey("proyecto.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)


# ------------------------------------------------------------------
# Publicaciones
# ------------------------------------------------------------------

class CategoriaPublicacion(db.Model):
    __tablename__ = "categoria_publicacion"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), unique=True, nullable=False)


class Publicacion(db.Model):
    __tablename__ = "publicacion"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(250), nullable=False)
    contenido = db.Column(db.Text)
    # Publicada | En revisión | Oculta
    estado = db.Column(db.String(20), nullable=False, default="En revisión")
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    semillero_id = db.Column(db.Integer, db.ForeignKey("semillero.id"))
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria_publicacion.id"), nullable=False)

    autor = db.relationship("Usuario")
    semillero = db.relationship("Semillero")
    categoria = db.relationship("CategoriaPublicacion")


class EvidenciaPublicacion(db.Model):
    __tablename__ = "evidencia_publicacion"

    id = db.Column(db.Integer, primary_key=True)
    publicacion_id = db.Column(db.Integer, db.ForeignKey("publicacion.id"), nullable=False)
    tipo = db.Column(db.String(10), nullable=False, default="enlace")  # enlace | archivo
    url = db.Column(db.String(500), nullable=False)


class ReaccionPublicacion(db.Model):
    __tablename__ = "reaccion_publicacion"
    __table_args__ = (db.UniqueConstraint("publicacion_id", "usuario_id"),)

    id = db.Column(db.Integer, primary_key=True)
    publicacion_id = db.Column(db.Integer, db.ForeignKey("publicacion.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default="me_gusta")
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)


class ComentarioPublicacion(db.Model):
    __tablename__ = "comentario_publicacion"

    id = db.Column(db.Integer, primary_key=True)
    publicacion_id = db.Column(db.Integer, db.ForeignKey("publicacion.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)

    usuario = db.relationship("Usuario")


class CompartidoPublicacion(db.Model):
    __tablename__ = "compartido_publicacion"

    id = db.Column(db.Integer, primary_key=True)
    publicacion_id = db.Column(db.Integer, db.ForeignKey("publicacion.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)


class VisualizacionPublicacion(db.Model):
    __tablename__ = "visualizacion_publicacion"

    id = db.Column(db.Integer, primary_key=True)
    publicacion_id = db.Column(db.Integer, db.ForeignKey("publicacion.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)


# ------------------------------------------------------------------
# Eventos y convocatorias
# ------------------------------------------------------------------

class Evento(db.Model):
    __tablename__ = "evento"

    id = db.Column(db.Integer, primary_key=True)
    semillero_id = db.Column(db.Integer, db.ForeignKey("semillero.id"))
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    fecha = db.Column(db.Date)
    modalidad = db.Column(db.String(20), nullable=False, default="Presencial")
    estado = db.Column(db.String(20), nullable=False, default="Abierta")

    semillero = db.relationship("Semillero")


class ParticipacionEvento(db.Model):
    __tablename__ = "participacion_evento"

    evento_id = db.Column(db.Integer, db.ForeignKey("evento.id"), primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=utcnow)


class Convocatoria(db.Model):
    __tablename__ = "convocatoria"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    cierre = db.Column(db.Date)
    estado = db.Column(db.String(20), nullable=False, default="Abierta")
    fecha_publicacion = db.Column(db.DateTime, nullable=False, default=utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))


class Postulacion(db.Model):
    __tablename__ = "postulacion"
    __table_args__ = (db.UniqueConstraint("convocatoria_id", "usuario_id"),)

    id = db.Column(db.Integer, primary_key=True)
    convocatoria_id = db.Column(db.Integer, db.ForeignKey("convocatoria.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    semillero_id = db.Column(db.Integer, db.ForeignKey("semillero.id"))
    nota = db.Column(db.Text)
    estado = db.Column(db.String(20), nullable=False, default="Enviada")
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)


# ------------------------------------------------------------------
# Logros, productos y gamificación
# ------------------------------------------------------------------

class TipoLogro(db.Model):
    __tablename__ = "tipo_logro"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), unique=True, nullable=False)
    xp = db.Column(db.Integer, nullable=False, default=50)


class Logro(db.Model):
    __tablename__ = "logro"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    tipo_logro_id = db.Column(db.Integer, db.ForeignKey("tipo_logro.id"), nullable=False)
    descripcion = db.Column(db.String(300), nullable=False)
    # Pendiente | Aprobado | Rechazado
    estado = db.Column(db.String(20), nullable=False, default="Pendiente")
    observacion = db.Column(db.String(300))
    validador_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    fecha_registro = db.Column(db.DateTime, nullable=False, default=utcnow)
    fecha_validacion = db.Column(db.DateTime)

    usuario = db.relationship("Usuario", foreign_keys=[usuario_id])
    validador = db.relationship("Usuario", foreign_keys=[validador_id])
    tipo = db.relationship("TipoLogro")


class EvidenciaLogro(db.Model):
    __tablename__ = "evidencia_logro"

    id = db.Column(db.Integer, primary_key=True)
    logro_id = db.Column(db.Integer, db.ForeignKey("logro.id"), nullable=False)
    tipo = db.Column(db.String(10), nullable=False, default="enlace")
    url = db.Column(db.String(500), nullable=False)


class ProductoSemillero(db.Model):
    __tablename__ = "producto_semillero"

    id = db.Column(db.Integer, primary_key=True)
    semillero_id = db.Column(db.Integer, db.ForeignKey("semillero.id"), nullable=False)
    tipo = db.Column(db.String(40), nullable=False)
    titulo = db.Column(db.String(250), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), nullable=False, default="Pendiente")
    validador_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)

    semillero = db.relationship("Semillero")


class Insignia(db.Model):
    __tablename__ = "insignia"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    descripcion = db.Column(db.String(250))
    destino = db.Column(db.String(10), nullable=False, default="usuario")  # usuario | semillero
    criterio = db.Column(db.String(30), nullable=False)  # logros | xp | publicaciones | proyectos
    valor = db.Column(db.Integer, nullable=False, default=1)


class UsuarioInsignia(db.Model):
    __tablename__ = "usuario_insignia"

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    insignia_id = db.Column(db.Integer, db.ForeignKey("insignia.id"), primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)

    insignia = db.relationship("Insignia")


class SemilleroInsignia(db.Model):
    __tablename__ = "semillero_insignia"

    semillero_id = db.Column(db.Integer, db.ForeignKey("semillero.id"), primary_key=True)
    insignia_id = db.Column(db.Integer, db.ForeignKey("insignia.id"), primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)

    insignia = db.relationship("Insignia")


class HistorialXP(db.Model):
    """Libro de XP: la fuente de verdad del puntaje, nivel y ranking."""

    __tablename__ = "historial_xp"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), index=True)
    semillero_id = db.Column(db.Integer, db.ForeignKey("semillero.id"), index=True)
    logro_id = db.Column(db.Integer, db.ForeignKey("logro.id"))
    producto_id = db.Column(db.Integer, db.ForeignKey("producto_semillero.id"))
    xp = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)


# ------------------------------------------------------------------
# Notificaciones, auditoría y configuración
# ------------------------------------------------------------------

class Notificacion(db.Model):
    __tablename__ = "notificacion"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True)
    tipo = db.Column(db.String(30), nullable=False)
    mensaje = db.Column(db.String(300), nullable=False)
    leida = db.Column(db.Boolean, nullable=False, default=False)
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)
    referencia_tipo = db.Column(db.String(30))
    referencia_id = db.Column(db.Integer)


class Bitacora(db.Model):
    __tablename__ = "bitacora"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    accion = db.Column(db.String(60), nullable=False)
    detalle = db.Column(db.String(500))
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow)

    usuario = db.relationship("Usuario")


class Configuracion(db.Model):
    __tablename__ = "configuracion"

    clave = db.Column(db.String(60), primary_key=True)
    valor = db.Column(db.String(200))
