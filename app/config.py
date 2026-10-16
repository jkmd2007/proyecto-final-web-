import os

class Config:
    
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://Riul_user:Riul_password@db:3306/Ruil_db"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "super-clave-secret"
    )
    
    #3600 Segundos = 1 Hora
    JWT_ACCESS_TOKEN_EXPIRES = 3600