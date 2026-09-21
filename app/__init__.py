from flask import Flask
from flask_jwt_extended import JWTManager

#importamos las configuraciones
from app.config import Config
from app.extencions import db
#manejo de las rutas con el blueprint

def create_app():
    app = Flask(
        __name__
        static_folder="static"
        template_folder= "template"
    )

    
# cargamos la configuracion
    app.config.from_object(Config)

#inicializamos la bd con app
    db.init_app(app)

#inicializamos el jwt
    JWTManager(app)
#registramos las rutas
#API auth

    with app.app_context():
    #inicializamos los modelos
    
    #creamos la bd
    
        return app