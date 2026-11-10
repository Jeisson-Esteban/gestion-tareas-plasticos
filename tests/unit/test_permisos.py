"""CP-04 · Tabla de decisión (nivel unitario).

Los casos salen de la misma MATRIZ que usa la app: la tabla es requisito y
prueba a la vez. Las celdas "centinela" están escritas a mano para que un
cambio accidental en la matriz también se detecte.
"""

import pytest

from app.permisos import ACCIONES, MATRIZ, RELACIONES, casos_matriz, puede


@pytest.mark.parametrize("rol, relacion, accion, permitido", list(casos_matriz()))
def test_puede_coincide_con_la_matriz(rol, relacion, accion, permitido):
    assert puede(rol, relacion, accion) is permitido


def test_la_matriz_cubre_todas_las_combinaciones():
    casos = list(casos_matriz())
    assert len(casos) == len(MATRIZ) * len(RELACIONES) * len(ACCIONES)  # 3 x 3 x 4 = 36


@pytest.mark.parametrize("rol, relacion, accion, esperado", [
    ("operario", "ajena", "ver", False),
    ("supervisor", "ajena", "ver", True),
    ("supervisor", "ajena", "completar", False),
    ("operario", "asignada", "editar", False),
    ("operario", "asignada", "completar", True),
    ("admin", "ajena", "eliminar", True),
])
def test_celdas_centinela(rol, relacion, accion, esperado):
    assert puede(rol, relacion, accion) is esperado


@pytest.mark.parametrize("rol, relacion, accion", [
    ("invitado", "creada", "ver"),      # rol desconocido
    ("admin", "otra", "ver"),           # relación desconocida
    ("admin", "creada", "imprimir"),    # acción desconocida
    ("operario", "cualquiera", "ver"),  # 'cualquiera' no es una relación real
])
def test_entradas_desconocidas_se_niegan(rol, relacion, accion):
    assert puede(rol, relacion, accion) is False
