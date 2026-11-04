# RIUL · Red de Investigación Universidad Libre

Aplicación Flask (API REST + SPA en HTML/CSS/JS) para gestionar semilleros de investigación:
usuarios y roles, semilleros, proyectos, publicaciones, eventos, convocatorias, logros,
gamificación (XP, niveles, insignias, ranking), notificaciones, reportes e indicadores.

# Ejecutar

**Con Docker (MySQL 8):**

```bash
docker compose up --build
```

Abrir <http://localhost:5000>. Las tablas y los datos iniciales se crean automáticamente la primera vez.

**Sin Docker (SQLite):**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Cuentas de demostración (`SEED_DEMO=1`)

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@unilibre.edu.co` | `Admin2026*` |
| Docente Líder (DataLab) | `docente@unilibre.edu.co` | `Docente2026*` |
| Estudiante Investigador | `estudiante@unilibre.edu.co` | `Estudiante2026*` |
| Otros usuarios demo | `carlos.perez@…`, `ana.gomez@…`, `luis.mora@…`, `camilo.herrera@…` | `Riul2026*` |

Hay dos solicitudes de registro pendientes (Sofía Vega, Valentina Cruz) para probar la validación.
Los registros nuevos quedan **pendientes** hasta que un administrador los apruebe.
**En producción** pon `SEED_DEMO=0`, cambia `ADMIN_PASSWORD`, `SECRET_KEY` y `JWT_SECRET_KEY`.

## Variables de entorno

`DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, `JWT_EXPIRES_SECONDS`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`,
`SEED_DEMO`, `INSTITUTIONAL_DOMAIN`, `UPLOAD_FOLDER`, `RESET_CODE_IN_RESPONSE` (solo desarrollo),
`MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_SENDER`.
Sin `MAIL_SERVER` los correos (recuperación, aprobación) se escriben en el log del servidor.

## Estructura (MVC)

```
app/
  models/entities.py      MODELO: tablas y relaciones (3FN)
  repositories/           ACCESO A DATOS: único lugar con consultas (db.session / Model.query)
      usuarios · academico · semilleros · proyectos · publicaciones · eventos · logros · gamificacion · sistema
  controllers/            CONTROLADOR: lógica de cada petición
      auth_controller · admin_controller · docente_controller · publico_controller · web_controller
  routes/                 Rutas: solo mapean URL + rol requerido -> controlador (API bajo /api)
  templates/ + static/    VISTA: index.html, partials, CSS y JS (api.js · app.js · roles.js · student.js)
  services/               Reglas de negocio reutilizables (gamificación, indicadores, seed, correo...)
  schemas/serializers.py  Modelo -> JSON que consume la vista
  utils/helpers.py        Respuestas, JWT por rol, bitácora, notificaciones
tests/test_api.py         Pruebas (pytest)
REQUISITOS_CUMPLIMIENTO.md  Trazabilidad RF/RNF -> implementación
```

Flujo de una petición: `routes/*.py` (URL y permisos) → `controllers/*_controller.py` (valida y orquesta)
→ `services` (reglas) y `repositories` (consultas) → `models` → `schemas/serializers.py` → JSON → vista (JS/HTML).

Convención: los controladores y servicios **no** usan `db.session` ni `Model.query`; piden los datos con
`from app import repositories as repo` (p. ej. `repo.usuarios.por_email(...)`) y confirman la transacción
con `repo.commit()`. Una prueba (`test_controladores_no_consultan_la_base_directamente`) lo vigila.

## API (resumen)

| Módulo | Endpoints |
|---|---|
| Auth | `POST /api/auth/register · login · logout · recover · reset · password`, `GET/PUT /api/auth/me` |
| Público | `GET /api/catalogos`, `/api/public/semilleros[/:id]`, `/public/proyectos`, `/public/publicaciones[/:id]`, `/public/eventos`, `/public/ranking`, `/public/indicadores`, `/api/convocatorias` |
| Estudiante / usuario | vinculación y seguimiento de semilleros, reacciones/comentarios/compartir, participar en eventos, postular, `GET/POST /api/me/logros`, `GET /api/me/cv`, notificaciones, `POST /api/uploads` |
| Docente líder | `/api/docente/` semillero (`POST` crea, `GET/PUT` consulta/edita), integrantes, proyectos (+avances), publicaciones, eventos, logros, productos |
| Administrador | `/api/admin/` users (+approve/reject/role), semilleros, proyectos, eventos, convocatorias, publicaciones, logros, productos, facultades, programas, bitácora, indicadores, reportes CSV, config/ranking |

Respuestas: `{"data": ..., "message": ...}`; errores: `{"message": ...}`.

## Reglas de negocio destacadas

- XP, nivel (1–5 estrellas: 0/300/800/1500/3000 XP), insignias y ranking se calculan desde `historial_xp`.
- Un logro aprobado asigna XP al usuario y a sus semilleros, otorga insignias y notifica. Los logros de un
  integrante los valida su docente líder; los del docente, un administrador.
- Los estudiantes proponen publicaciones («En revisión»); al publicarse se notifica a los seguidores del semillero.
- Evidencias: enlaces http(s) o archivos (pdf, png, jpg, docx, pptx, xlsx, máx. 5 MB, con verificación de firma).
- Seguridad: contraseñas con hash+sal (Werkzeug), JWT, control de acceso por rol en el servidor, bitácora de
  acciones críticas, recuperación con código de 6 dígitos que vence en 15 minutos.

## Pruebas

```bash
pip install pytest && python -m pytest -q
```

## Pendiente / fuera del alcance del código

- HTTPS/TLS (RNF-04), copias de seguridad (RNF-15) y disponibilidad 99 % (RNF-14) se resuelven en la infraestructura
  (proxy inverso con certificado, respaldo del volumen `mysql_data`, orquestación).
- Envío real de correo: configurar `MAIL_*`.
- Notificaciones en tiempo real (WebSockets): hoy se consultan al abrir la pantalla.
- Los archivos subidos se guardan en el disco del contenedor (volumen `uploads_data`); para producción usar almacenamiento de objetos.
