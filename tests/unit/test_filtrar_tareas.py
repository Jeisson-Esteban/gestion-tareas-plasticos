"""CP-06 · Regresión de DEF-01 (#10) a nivel unitario.

La prueba de integración ya detecta el defecto por HTTP; esta lo fija en la
función pura, así el fallo apunta directo a filtrar_tareas y no a la API.
"""

from app.servicios import filtrar_tareas

TAREAS = [
    {"titulo": "Limpiar tolva", "descripcion": None, "estado": "pendiente"},
    {"titulo": "Cambiar molde 7", "descripcion": None, "estado": "en_progreso"},
    {"titulo": "Revisar molde 3", "descripcion": None, "estado": "completada"},
]


def test_pendientes_son_todas_las_no_completadas():
    titulos = [t["titulo"] for t in filtrar_tareas(TAREAS, estado="pendientes")]
    assert titulos == ["Limpiar tolva", "Cambiar molde 7"]


def test_tarea_sin_descripcion_no_coincide_con_cualquier_texto():
    # Una descripción vacía no debe "contener" nada. mutmut cambió el `or ""`
    # por `or "XXXX"` y ninguna prueba lo notó, porque todas las búsquedas
    # coincidían por el título.
    assert filtrar_tareas(TAREAS, q="xx") == []
