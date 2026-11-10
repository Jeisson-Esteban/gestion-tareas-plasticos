"""CP-01 (título), CP-02 (fecha límite) y CP-03 (contraseña) · Valores límite.

Los defectos se concentran en los bordes (>= contra >, strip antes o después
de medir), así que se prueba justo a cada lado de cada límite.
"""

from datetime import date, timedelta

import pytest

from app.servicios import (
    normalizar_email,
    validar_contrasena,
    validar_email,
    validar_fecha_limite,
    validar_registro,
    validar_tarea_nueva,
    validar_titulo,
)

HOY = date(2026, 11, 9)


# CP-01
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


# CP-02: HOY es fijo para que el resultado no dependa del día en que corra la prueba
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


# CP-03
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


# Se compara el dict completo y no solo sus claves: mutmut mostró que
# `errores["email"] = None` sobrevivía porque la clave seguía ahí. La API
# devuelve estos textos en "detalles", así que el mensaje también es requisito.
def test_registro_reporta_cada_campo_invalido():
    errores = validar_registro({"email": "x", "contrasena": "corta", "nombre": "  "})
    assert errores == {
        "email": "Email inválido",
        "contrasena": "La contraseña debe tener al menos 8 caracteres",
        "nombre": "El nombre es obligatorio",
    }


def test_registro_sin_campos_reporta_email_y_nombre():
    # Sin "nombre" en absoluto (no solo vacío): cubre el `or ""` del servicio.
    errores = validar_registro({"contrasena": "abcd1234"})
    assert errores == {"email": "Email inválido", "nombre": "El nombre es obligatorio"}


def test_normalizar_email_vacio_da_texto_vacio():
    assert normalizar_email(None) == ""
    assert normalizar_email("  Ana@Planta.CO ") == "ana@planta.co"


def test_tarea_nueva_valida():
    datos = {"titulo": "Cambiar molde", "fecha_limite": HOY.isoformat(), "asignado_id": 1}
    assert validar_tarea_nueva(datos, HOY) == {}


def test_tarea_nueva_reporta_cada_campo_invalido():
    datos = {"titulo": "", "fecha_limite": "2020-01-01", "asignado_id": "x"}
    assert validar_tarea_nueva(datos, HOY) == {
        "titulo": "El título es obligatorio",
        "fecha_limite": "La fecha límite no puede ser anterior a hoy",
        "asignado_id": "Debe indicar un usuario asignado válido",
    }


# Mensajes exactos que ve el usuario. Las pruebas de valores límite (CP-01 a
# CP-03) solo miraban si había error; con eso sobrevivían mutantes que
# cambiaban el texto por "XX...XX" o lo pasaban a mayúsculas.
@pytest.mark.parametrize("error, esperado", [
    (lambda: validar_titulo("   "), "El título es obligatorio"),                               # CP-01
    (lambda: validar_fecha_limite("09/11/2026", HOY), "Fecha inválida, use el formato AAAA-MM-DD"),  # CP-02
    (lambda: validar_fecha_limite(HOY - timedelta(days=1), HOY),
     "La fecha límite no puede ser anterior a hoy"),                                            # CP-02
    (lambda: validar_contrasena("abcdefgh"),
     "La contraseña debe tener al menos una letra y un número"),                                # CP-03
    (lambda: validar_email("ana@planta"), "Email inválido"),
], ids=["titulo", "fecha-formato", "fecha-pasada", "contrasena-composicion", "email"])
def test_mensajes_de_error_exactos(error, esperado):
    assert error() == esperado
