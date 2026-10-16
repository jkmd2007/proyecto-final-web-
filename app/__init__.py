import time
from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from sqlalchemy.exc import OperationalError

# Importamos las configuraciones y extensiones
from app.config import Config
from app.extensions import db

def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    # 1. Cargamos la configuración primero
    app.config.from_object(Config)

    # 2. Inicializamos la bd y el JWT con la app
    db.init_app(app)
    JWTManager(app)

    # 3. Ahora sí, con la app ya configurada e inicializada, hacemos los reintentos
    with app.app_context():
        for i in range(10):
            try:
                db.create_all()
                print("¡Base de datos conectada y tablas creadas con éxito!")
                break
            except OperationalError as e:
                print(f"Intento {i+1}/10: La base de datos aún no está lista ({e}), reintentando en 3 segundos...")
                time.sleep(3)

    # 4. Definimos la ruta principal aquí dentro
    @app.route('/')
    def home():
        return render_template('index.html')

    return app