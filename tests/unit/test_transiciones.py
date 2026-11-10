"""CP-05 · Transición de estados (reabrir y reasignar una tarea completada).

Se prueban los 9 pares posibles y no solo los permitidos: el riesgo real es
que una transición prohibida (completada -> pendiente sin reabrir) pase.
"""

import itertools

import pytest

from app.servicios import ESTADOS, puede_reabrir, puede_reasignar, puede_transicionar

PERMITIDAS = {
    ("pendiente", "en_progreso"),
    ("en_progreso", "completada"),
    ("pendiente", "completada"),
}


@pytest.mark.parametrize("desde, hacia", list(itertools.product(ESTADOS, ESTADOS)))
def test_transiciones_normales(desde, hacia):
    assert puede_transicionar(desde, hacia) == ((desde, hacia) in PERMITIDAS)


def test_completada_a_pendiente_solo_con_reabrir():
    assert puede_transicionar("completada", "pendiente") is False
    assert puede_transicionar("completada", "pendiente", accion="reabrir") is True


@pytest.mark.parametrize("desde, hacia", [
    ("pendiente", "pendiente"),
    ("en_progreso", "pendiente"),
    ("completada", "en_progreso"),
])
def test_reabrir_no_sirve_para_otras_transiciones(desde, hacia):
    assert puede_transicionar(desde, hacia, accion="reabrir") is False


def test_accion_desconocida_no_permite_nada():
    assert puede_transicionar("completada", "pendiente", accion="borrar") is False


@pytest.mark.parametrize("rol, relacion, esperado", [
    ("operario", "creada", True),
    ("operario", "asignada", False),
    ("supervisor", "creada", True),
    ("supervisor", "asignada", False),
    ("supervisor", "ajena", False),
    ("admin", "ajena", True),
])
def test_quien_puede_reabrir(rol, relacion, esperado):
    assert puede_reabrir(rol, relacion) == esperado


@pytest.mark.parametrize("estado, esperado", [
    ("pendiente", True),
    ("en_progreso", True),
    ("completada", False),   # primero hay que reabrirla
])
def test_reasignar(estado, esperado):
    assert puede_reasignar(estado) == esperado
