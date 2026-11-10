"""Cambio de contraseña: exige la actual y la anterior deja de servir.

Complementa CP-03: la regla de contraseña también se aplica al cambiarla,
no solo al registrarse.
"""

from tests.conftest import CLAVE, USUARIOS

EMAIL = USUARIOS["operario"][0]
NUEVA = "NuevaClave99"


def test_cambio_de_contrasena_invalida_la_anterior(preparar_escenario, cliente):
    c = preparar_escenario.cliente("operario")
    r = c.put("/api/perfil/contrasena", json={"actual": CLAVE, "nueva": NUEVA})
    assert r.status_code == 200
    c.post("/api/logout")

    assert cliente.post("/api/login", json={"email": EMAIL, "contrasena": CLAVE}).status_code == 401
    assert cliente.post("/api/login", json={"email": EMAIL, "contrasena": NUEVA}).status_code == 200


def test_exige_la_contrasena_actual_correcta(preparar_escenario):
    c = preparar_escenario.cliente("operario")
    r = c.put("/api/perfil/contrasena", json={"actual": "equivocada1", "nueva": NUEVA})
    assert r.status_code == 400


def test_la_nueva_contrasena_debe_cumplir_las_reglas(preparar_escenario):
    c = preparar_escenario.cliente("operario")
    r = c.put("/api/perfil/contrasena", json={"actual": CLAVE, "nueva": "corta1"})
    assert r.status_code == 400
