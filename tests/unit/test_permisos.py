"""CP-04 · Tabla de decisión (nivel unitario).

Los casos salen de la misma MATRIZ que usa la app: la tabla es requisito y
prueba a la vez. Las celdas "centinela" están escritas a mano para que un
cambio accidental en la matriz también se detecte.
"""

import pytest

from app.permisos import ACCIONES, MATRIZ, RELACIONES, _fila, casos_matriz, puede


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


def test_cada_fila_usa_exactamente_los_nombres_de_las_acciones():
    # puede() hace fila.get(accion, False): si una clave quedara mal escrita
    # ("VER" en vez de "ver"), el permiso se negaría en silencio y nadie lo
    # notaría. mutmut lo mostró: esas mutaciones de _fila sobrevivían.
    assert _fila(True, False, True, False) == {
        "ver": True, "editar": False, "completar": True, "eliminar": False}
    assert set(_fila(True, True, True, True)) == set(ACCIONES)


def test_celda_faltante_en_la_matriz_se_niega(monkeypatch):
    # Si alguien agrega un rol sin llenar todas sus relaciones, la regla debe
    # fallar cerrada (negar), no abrir el permiso. Con la MATRIZ actual esa
    # rama no se alcanza, por eso mutmut la marcó como sobreviviente.
    monkeypatch.setitem(MATRIZ, "auditor", {"creada": _fila(True, False, False, False)})
    assert puede("auditor", "creada", "ver") is True
    assert puede("auditor", "ajena", "ver") is False
