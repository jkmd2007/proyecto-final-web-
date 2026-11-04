import os


def _flag(name, default="0"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "si", "sí")


class Config:

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///riul.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Reconecta si MySQL cerró la conexión inactiva
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "development-secret"
    )

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "super-clave-secret"
    )

    #3600 Segundos = 1 Hora
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_EXPIRES_SECONDS", "3600"))

    # Correo institucional de la Universidad Libre
    INSTITUTIONAL_DOMAIN = os.getenv("INSTITUTIONAL_DOMAIN", "unilibre.edu.co")

    # Archivos de evidencia (RNF-05)
    MAX_UPLOAD_BYTES = 5 * 1024 * 1024
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "")

    # Recuperación de contraseña. Sin servidor de correo el código solo se
    # escribe en el log; con RESET_CODE_IN_RESPONSE=1 también se devuelve
    # en la respuesta (SOLO para desarrollo).
    RESET_CODE_IN_RESPONSE = _flag("RESET_CODE_IN_RESPONSE", "0")

    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = _flag("MAIL_USE_TLS", "1")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_SENDER = os.getenv("MAIL_SENDER", "RIUL <no-reply@unilibre.edu.co>")

    # Datos iniciales
    ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador RIUL")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@unilibre.edu.co")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin2026*")
    SEED_DEMO = _flag("SEED_DEMO", "1")
