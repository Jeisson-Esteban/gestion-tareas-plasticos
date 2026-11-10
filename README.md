# Gestión de tareas · planta de plásticos

App Flask mínima (API JSON y dos vistas HTML) que sirve de sistema bajo prueba: tiene
autenticación, roles, estados, filtros y bloqueo optimista para que las pruebas tengan
reglas concretas que verificar.

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/WSL: source .venv/bin/activate
pip install -r requirements.txt

flask --app app sembrar         # admin@, supervisor@ y operario@planta.local / Clave1234
flask --app app run             # http://127.0.0.1:5000/login
```

## Pruebas

```bash
pytest -m "not e2e" --cov=app --cov-report=term-missing   # unitarias + integración
pytest -m e2e                                             # Selenium (requiere Chrome)
mutmut run && mutmut results                              # solo en WSL/Linux
```

## Estructura

| Ruta | Contenido |
|---|---|
| `app/permisos.py` | `MATRIZ` de permisos y `puede(rol, relacion, accion)` |
| `app/servicios.py` | Validaciones, transiciones, visibilidad y filtros (funciones puras) |
| `app/db.py` | Esquema SQLite y consultas |
| `app/rutas_api.py` | API JSON (`/api/...`) |
| `app/rutas_web.py` | `/login` y `/panel` para Selenium |
| `tests/` | `unit/`, `integracion/`, `e2e/` y `conftest.py` |
| `docs/` | Plan de pruebas y resultados |

## API

| Método | Ruta | Respuestas |
|---|---|---|
| POST | `/api/registro` | 201 · 400 inválido · 409 email existente |
| POST | `/api/login` | 200 · 401 con el mismo mensaje si falla el email o la contraseña |
| POST | `/api/logout` | 200 |
| GET | `/api/tareas?estado=&q=` | Solo las tareas que el usuario puede ver |
| POST | `/api/tareas` | 201 · 400 |
| GET | `/api/tareas/<id>` | 200 · 403 · 404 |
| PUT | `/api/tareas/<id>` | Exige `version` · 400 · 403 · 409 conflicto |
| POST | `/api/tareas/<id>/completar` | 200 · 400 si ya está completada · 403 |
| POST | `/api/tareas/<id>/reabrir` | Solo el creador o un admin · 400 · 403 |
| DELETE | `/api/tareas/<id>` | 204 · 403 |
| PUT | `/api/perfil/contrasena` | Exige `actual` y `nueva` · 400 |

Sin sesión, todo responde 401 (excepto registro y login).

> **Defecto sembrado a propósito:** `estado=pendientes` omite las tareas `en_progreso`.
> Ver [docs/plan-de-pruebas.md](docs/plan-de-pruebas.md#defecto-sembrado-def-01).
