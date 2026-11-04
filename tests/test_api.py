

"""
Pruebas de humo del API de RIUL.

Ejecutar desde la raíz del proyecto:
    pip install pytest
    python -m pytest -q
Usa SQLite en memoria y los datos de demostración.
"""

import io
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["RESET_CODE_IN_RESPONSE"] = "1"
os.environ["SEED_DEMO"] = "1"

import pytest  # noqa: E402

from app import create_app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth(client, email, password):
    response = login(client, email, password)
    assert response.status_code == 200, response.get_json()
    return {"Authorization": "Bearer " + response.get_json()["data"]["access_token"]}


ADMIN = ("admin@unilibre.edu.co", "Admin2026*")
DOCENTE = ("docente@unilibre.edu.co", "Docente2026*")
ESTUDIANTE = ("estudiante@unilibre.edu.co", "Estudiante2026*")


def test_login_y_credenciales_invalidas(client):
    assert login(client, *ADMIN).status_code == 200
    assert login(client, ADMIN[0], "incorrecta1").status_code == 401


def test_roles_y_permisos(client):
    assert client.get("/api/admin/users").status_code == 401
    student = auth(client, *ESTUDIANTE)
    assert client.get("/api/admin/users", headers=student).status_code == 403
    assert client.get("/api/docente/semillero", headers=student).status_code == 403


def test_registro_pendiente_y_aprobacion(client):
    payload = {
        "name": "Nuevo Usuario", "email": "nuevo@unilibre.edu.co", "password": "Clave2026x",
        "faculty": "Ingeniería", "program": "Ingeniería de Sistemas", "institutional": True
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409
    assert login(client, payload["email"], payload["password"]).status_code == 403

    admin = auth(client, *ADMIN)
    users = client.get("/api/admin/users", headers=admin).get_json()["data"]
    new_id = next(u["id"] for u in users if u["correo"] == payload["email"])

    response = client.patch(f"/api/admin/users/{new_id}/approve", headers=admin,
                            json={"rol": "Estudiante Investigador"})
    assert response.status_code == 200
    assert login(client, payload["email"], payload["password"]).status_code == 200


def test_validacion_de_logro_asigna_xp(client):
    student = auth(client, *ESTUDIANTE)
    before = client.get("/api/me/cv", headers=student).get_json()["data"]["xp"]

    created = client.post("/api/me/logros", headers=student, json={
        "descripcion": "Premio de prueba", "tipo": "Artículo", "evidencia": "https://ejemplo.com/prueba"
    })
    assert created.status_code == 201
    logro_id = created.get_json()["data"]["id"]

    # Sin evidencia no se puede enviar
    assert client.post("/api/me/logros", headers=student,
                       json={"descripcion": "x", "tipo": "Artículo"}).status_code == 400

    docente = auth(client, *DOCENTE)
    resolved = client.patch(f"/api/docente/logros/{logro_id}", headers=docente, json={"estado": "Aprobado"})
    assert resolved.status_code == 200

    after = client.get("/api/me/cv", headers=student).get_json()["data"]["xp"]
    assert after == before + 300


def test_consulta_publica_sin_sesion(client):
    assert client.get("/api/public/semilleros").status_code == 200
    assert client.get("/api/public/ranking?tipo=estudiantes").get_json()["data"]["publicado"] is True
    assert client.get("/api/convocatorias").status_code == 200
    assert client.get("/api/catalogos").get_json()["data"]["facultades"]


def test_recuperacion_de_contrasena(client):
    response = client.post("/api/auth/recover", json={"email": ESTUDIANTE[0]})
    code = response.get_json()["data"]["code"]

    assert client.post("/api/auth/reset", json={
        "email": ESTUDIANTE[0], "code": "000000", "password": "Otra2026clave"
    }).status_code == 400

    assert client.post("/api/auth/reset", json={
        "email": ESTUDIANTE[0], "code": code, "password": "Estudiante2026*"
    }).status_code == 200


def test_subida_valida_formato(client):
    student = auth(client, *ESTUDIANTE)

    bad = client.post("/api/uploads", headers=student, content_type="multipart/form-data",
                      data={"file": (io.BytesIO(b"no soy un pdf"), "x.pdf")})
    assert bad.status_code == 400

    good = client.post("/api/uploads", headers=student, content_type="multipart/form-data",
                       data={"file": (io.BytesIO(b"%PDF-1.4 contenido"), "x.pdf")})
    assert good.status_code == 201
    assert good.get_json()["data"]["url"].startswith("/api/files/")


def test_ranking_oculto_por_admin(client):
    admin = auth(client, *ADMIN)
    assert client.put("/api/admin/config/ranking", headers=admin, json={"publicado": False}).status_code == 200
    assert client.get("/api/public/ranking").get_json()["data"]["publicado"] is False
    client.put("/api/admin/config/ranking", headers=admin, json={"publicado": True})


# ------------------------------------------------------------------
# RF-15: el docente líder crea su semillero
# ------------------------------------------------------------------

def _docente_sin_semillero(client):
    """Crea (como admin) un docente activo sin semillero y devuelve sus credenciales."""
    admin = auth(client, *ADMIN)
    response = client.post("/api/admin/users", headers=admin, json={
        "nombre": "Docente Nuevo", "correo": "docente.nuevo@unilibre.edu.co",
        "rol": "Docente Líder", "facultad": "Derecho", "programa": "Derecho"
    })
    assert response.status_code == 201, response.get_json()
    return ("docente.nuevo@unilibre.edu.co", response.get_json()["data"]["password_temporal"])


def test_docente_sin_semillero_recibe_404_y_puede_crearlo(client):
    headers = auth(client, *_docente_sin_semillero(client))

    assert client.get("/api/docente/semillero", headers=headers).status_code == 404

    # Campos obligatorios
    assert client.post("/api/docente/semillero", headers=headers, json={"nombre": "Solo nombre"}).status_code == 400

    created = client.post("/api/docente/semillero", headers=headers, json={
        "nombre": "JusticiaLab", "descripcion": "Derecho y tecnología",
        "linea": "Derecho digital", "facultad": "Derecho"
    })
    assert created.status_code == 201, created.get_json()
    assert created.get_json()["data"]["nombre"] == "JusticiaLab"

    # Ahora lidera uno: puede consultarlo pero no crear un segundo
    assert client.get("/api/docente/semillero", headers=headers).status_code == 200
    again = client.post("/api/docente/semillero", headers=headers, json={
        "nombre": "Otro", "descripcion": "x", "linea": "y", "facultad": "Derecho"
    })
    assert again.status_code == 409


def test_crear_semillero_nombre_duplicado_y_solo_docentes(client):
    student = auth(client, *ESTUDIANTE)
    assert client.post("/api/docente/semillero", headers=student, json={}).status_code == 403

    teacher = auth(client, "camilo.herrera@unilibre.edu.co", "Riul2026*")
    # Camilo ya lidera BioLibre
    assert client.post("/api/docente/semillero", headers=teacher, json={
        "nombre": "DataLab", "descripcion": "x", "linea": "y", "facultad": "Ingeniería"
    }).status_code == 409


# ------------------------------------------------------------------
# Capa de repositorios (MVC)
# ------------------------------------------------------------------

def test_repositorios_encapsulan_el_acceso_a_datos(client):
    from app import repositories as repo

    app = client.application
    with app.app_context():
        admin = repo.usuarios.por_email("admin@unilibre.edu.co")
        assert admin is not None and admin.es_admin
        assert repo.usuarios.contar_admins_activos() >= 1
        assert repo.roles.por_nombre("Rol inexistente") is None
        assert repo.facultades.activa_por_nombre("ingeniería") is not None
        assert repo.semilleros.por_nombre("  datalab ") is not None
        assert repo.historial_xp.total_global() >= 0
        assert repo.configuracion.valor("clave_que_no_existe", "x") == "x"


def test_controladores_no_consultan_la_base_directamente():
    """MVC: solo app/repositories (y modelos/fábrica) tocan db.session o Model.query."""
    root = os.path.join(os.path.dirname(__file__), "..", "app")
    permitidos = {"repositories", "models"}
    permitidos_archivos = {"__init__.py", "extencions.py"}

    for carpeta, _, archivos in os.walk(root):
        if os.path.basename(carpeta) in permitidos or "static" in carpeta or "templates" in carpeta:
            continue
        for nombre in archivos:
            if not nombre.endswith(".py") or (nombre in permitidos_archivos and carpeta == root):
                continue
            with open(os.path.join(carpeta, nombre), encoding="utf-8") as handle:
                contenido = handle.read()
            assert ".query" not in contenido and "db.session" not in contenido, os.path.join(carpeta, nombre)
