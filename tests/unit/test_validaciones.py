"""CP-01 · Valores límite.

Los defectos se concentran en los bordes (>= contra >, strip antes o después
de medir), así que se prueba justo a cada lado de cada límite.
"""

from datetime import date, timedelta

import pytest

from app.servicios import (
    validar_contrasena,
    validar_email,
    validar_fecha_limite,
    validar_registro,
    validar_tarea_nueva,
    validar_titulo,
)

HOY = date(2026, 11, 9)


@pytest.mark.parametrize("titulo, valido", [
    ("", False),                        # 0 caracteres
    ("a", True),                        # 1 (mínimo)
    ("a" * 200, True),                  # 200 (máximo)
    ("a" * 201, False),                 # 201 (máximo + 1)
    ("     ", False),                   # solo espacios
    ("  " + "a" * 200 + "  ", True),    # los espacios laterales no cuentan
    (None, False),
])
def test_titulo(titulo, valido):
    assert (validar_titulo(titulo) is None) == valido


@pytest.mark.parametrize("fecha, valida", [
    (HOY - timedelta(days=1), False),   # ayer
    (HOY, True),                        # hoy
    (HOY + timedelta(days=1), True),    # mañana
    ("2026-11-09", True),               # también acepta texto ISO
    ("09/11/2026", False),
    (None, False),
])
def test_fecha_limite(fecha, valida):
    assert (validar_fecha_limite(fecha, HOY) is None) == valida


@pytest.mark.parametrize("contrasena, valida", [
    ("abc1234", False),     # 7 caracteres
    ("abcd1234", True),     # 8 caracteres
    ("abcdefgh", False),    # sin número
    ("12345678", False),    # sin letra
    ("", False),
    (None, False),
])
def test_contrasena(contrasena, valida):
    assert (validar_contrasena(contrasena) is None) == valida


@pytest.mark.parametrize("email, valido", [
    ("ana@planta.co", True),
    ("ana@planta", False),
    ("ana.planta.co", False),
    ("", False),
])
def test_email(email, valido):
    assert (validar_email(email) is None) == valido


def test_registro_valido_no_tiene_errores():
    assert validar_registro({"email": "A@B.co ", "contrasena": "abcd1234", "nombre": "Ana"}) == {}


def test_registro_reporta_cada_campo_invalido():
    errores = validar_registro({"email": "x", "contrasena": "corta", "nombre": "  "})
    assert set(errores) == {"email", "contrasena", "nombre"}


def test_tarea_nueva_valida():
    datos = {"titulo": "Cambiar molde", "fecha_limite": HOY.isoformat(), "asignado_id": 1}
    assert validar_tarea_nueva(datos, HOY) == {}


def test_tarea_nueva_reporta_cada_campo_invalido():
    datos = {"titulo": "", "fecha_limite": "2020-01-01", "asignado_id": "x"}
    assert set(validar_tarea_nueva(datos, HOY)) == {"titulo", "fecha_limite", "asignado_id"}
