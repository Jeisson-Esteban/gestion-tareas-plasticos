from datetime import date

import pytest

from app import create_app, db

CLAVE = "Clave1234"

# clave -> (email, nombre, rol). "otro" es un segundo operario para armar
# tareas ajenas o creadas por alguien distinto al actor.
USUARIOS = {
    "operario": ("operario@planta.test", "Olga Operaria", "operario"),
    "otro": ("otro@planta.test", "Oscar Operario", "operario"),
    "supervisor": ("supervisor@planta.test", "Sara Supervisora", "supervisor"),
    "admin": ("admin@planta.test", "Ana Admin", "admin"),
}


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "pruebas",
        "DATABASE": str(tmp_path / "pruebas.sqlite"),
        # hash rápido para que la suite no tarde; en producción se usa scrypt
        "HASH_METODO": "pbkdf2:sha256:1000",
    })


@pytest.fixture
def cliente(app):
    return app.test_client()


class Escenario:
    def __init__(self, app, ids):
        self.app = app
        self.ids = ids

    def cliente(self, clave):
        """Cliente HTTP con sesión iniciada como el usuario indicado."""
        c = self.app.test_client()
        r = c.post("/api/login", json={"email": USUARIOS[clave][0], "contrasena": CLAVE})
        assert r.status_code == 200, r.get_json()
        return c

    def __call__(self, rol, relacion):
        """preparar_escenario(rol, relacion) -> (cliente del actor, tarea).

        Arma una fila de la tabla de decisión (CP-04): una tarea que tiene la
        relación pedida con un usuario del rol indicado. "otro" es siempre un
        operario distinto al actor, para que la relación sea inequívoca.
        """
        if relacion == "creada":
            tarea = nueva_tarea(self.cliente(rol), asignado_id=self.ids["otro"])
        else:
            asignado = rol if relacion == "asignada" else "otro"
            tarea = nueva_tarea(self.cliente("otro"), asignado_id=self.ids[asignado])
        return self.cliente(rol), tarea


@pytest.fixture
def preparar_escenario(app):
    with app.app_context():
        ids = {
            clave: db.crear_usuario(email, db.hashear(CLAVE), nombre, rol)
            for clave, (email, nombre, rol) in USUARIOS.items()
        }
    return Escenario(app, ids)


def nueva_tarea(cliente, **campos):
    datos = {"titulo": "Tarea de prueba", "fecha_limite": date.today().isoformat()}
    datos.update(campos)
    r = cliente.post("/api/tareas", json=datos)
    assert r.status_code == 201, r.get_json()
    return r.get_json()
