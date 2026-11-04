import os

from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager

from app.config import Config
from app.extencions import db
from app.routes.web_routes import web_bp


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)

    if not app.config["UPLOAD_FOLDER"]:
        app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, "uploads")

    db.init_app(app)

    jwt = JWTManager(app)

    # Respuestas JSON uniformes para errores de autenticación
    @jwt.unauthorized_loader
    def _missing_token(reason):
        return jsonify(message="Debes iniciar sesión"), 401

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return jsonify(message="Sesión no válida"), 401

    @jwt.expired_token_loader
    def _expired_token(header, payload):
        return jsonify(message="Tu sesión expiró. Inicia sesión de nuevo"), 401

    # Blueprints
    from app.routes.admin import bp as admin_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.docente import bp as docente_bp
    from app.routes.publico import bp as publico_bp

    # Register blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(docente_bp)
    app.register_blueprint(publico_bp)

    @app.errorhandler(404)
    def _not_found(error):
        if request.path.startswith("/api/"):
            return jsonify(message="Recurso no encontrado"), 404
        return error

    @app.errorhandler(405)
    def _not_allowed(error):
        if request.path.startswith("/api/"):
            return jsonify(message="Método no permitido"), 405
        return error

    @app.errorhandler(413)
    def _too_large(error):
        return jsonify(message="El archivo supera el tamaño máximo permitido"), 413

    @app.errorhandler(500)
    def _server_error(error):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify(message="Error interno del servidor"), 500
        return error

    @app.after_request
    def _security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response

    with app.app_context():
        from app import models  # noqa: F401  (registra las tablas)
        from app.services.seed import seed_base, seed_demo

        db.create_all()
        seed_base()
        seed_demo()

    return app
