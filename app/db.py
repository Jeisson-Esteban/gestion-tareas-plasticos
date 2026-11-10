"""Acceso a SQLite: conexión, esquema y consultas."""

import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

ESQUEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nombre        TEXT NOT NULL,
    rol           TEXT NOT NULL CHECK (rol IN ('operario', 'supervisor', 'admin'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo       TEXT NOT NULL,
    descripcion  TEXT,
    fecha_limite TEXT NOT NULL,
    estado       TEXT NOT NULL DEFAULT 'pendiente'
                 CHECK (estado IN ('pendiente', 'en_progreso', 'completada')),
    creador_id   INTEGER NOT NULL REFERENCES users(id),
    asignado_id  INTEGER NOT NULL REFERENCES users(id),
    version      INTEGER NOT NULL DEFAULT 1
);
"""

CAMPOS_EDITABLES = ("titulo", "descripcion", "fecha_limite", "estado", "asignado_id")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def init_db():
    get_db().executescript(ESQUEMA)


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(sembrar)
    with app.app_context():
        init_db()


def hashear(contrasena):
    return generate_password_hash(contrasena, method=current_app.config["HASH_METODO"])


def _dict(fila):
    return dict(fila) if fila is not None else None


# ---------- Usuarios ----------

def crear_usuario(email, password_hash, nombre, rol="operario"):
    """Lanza sqlite3.IntegrityError si el email ya existe."""
    conexion = get_db()
    cursor = conexion.execute(
        "INSERT INTO users (email, password_hash, nombre, rol) VALUES (?, ?, ?, ?)",
        (email, password_hash, nombre, rol),
    )
    conexion.commit()
    return cursor.lastrowid


def usuario_por_id(usuario_id):
    return _dict(get_db().execute("SELECT * FROM users WHERE id = ?", (usuario_id,)).fetchone())


def usuario_por_email(email):
    return _dict(get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone())


def listar_usuarios():
    filas = get_db().execute("SELECT id, nombre, rol FROM users ORDER BY nombre").fetchall()
    return [dict(f) for f in filas]


def actualizar_contrasena(usuario_id, password_hash):
    conexion = get_db()
    conexion.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, usuario_id))
    conexion.commit()


# ---------- Tareas ----------

def crear_tarea(titulo, descripcion, fecha_limite, creador_id, asignado_id):
    conexion = get_db()
    cursor = conexion.execute(
        "INSERT INTO tasks (titulo, descripcion, fecha_limite, creador_id, asignado_id)"
        " VALUES (?, ?, ?, ?, ?)",
        (titulo, descripcion, fecha_limite, creador_id, asignado_id),
    )
    conexion.commit()
    return cursor.lastrowid


def tarea_por_id(tarea_id):
    return _dict(get_db().execute("SELECT * FROM tasks WHERE id = ?", (tarea_id,)).fetchone())


def listar_tareas():
    return [dict(f) for f in get_db().execute("SELECT * FROM tasks ORDER BY id").fetchall()]


def actualizar_tarea(tarea_id, version, cambios):
    """Bloqueo optimista: solo actualiza si la versión sigue siendo la esperada.

    El chequeo y la escritura van en el mismo UPDATE, así no hay ventana
    entre leer la versión y guardar. Devuelve False si hubo conflicto.
    """
    columnas = [c for c in cambios if c in CAMPOS_EDITABLES]
    asignaciones = "".join(f"{c} = ?, " for c in columnas)
    conexion = get_db()
    cursor = conexion.execute(
        f"UPDATE tasks SET {asignaciones}version = version + 1 WHERE id = ? AND version = ?",
        [cambios[c] for c in columnas] + [tarea_id, version],
    )
    conexion.commit()
    return cursor.rowcount == 1


def cambiar_estado(tarea_id, estado):
    conexion = get_db()
    conexion.execute(
        "UPDATE tasks SET estado = ?, version = version + 1 WHERE id = ?", (estado, tarea_id)
    )
    conexion.commit()


def eliminar_tarea(tarea_id):
    conexion = get_db()
    conexion.execute("DELETE FROM tasks WHERE id = ?", (tarea_id,))
    conexion.commit()


# ---------- Datos de demostración ----------

USUARIOS_DEMO = [
    ("admin@planta.local", "Ana Admin", "admin"),
    ("supervisor@planta.local", "Sergio Supervisor", "supervisor"),
    ("operario@planta.local", "Olga Operaria", "operario"),
]
CONTRASENA_DEMO = "Clave1234"


@click.command("sembrar")
@with_appcontext
def sembrar():
    """Crea usuarios de demostración (contraseña: Clave1234)."""
    for email, nombre, rol in USUARIOS_DEMO:
        if usuario_por_email(email) is None:
            crear_usuario(email, hashear(CONTRASENA_DEMO), nombre, rol)
            click.echo(f"Creado {email} ({rol})")
