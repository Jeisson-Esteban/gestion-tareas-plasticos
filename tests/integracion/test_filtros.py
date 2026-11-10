"""CP-05 · Filtros por estado y búsqueda combinados (detecta DEF-01).

"pendientes" significa todo lo que aún no está completado (pendiente y
en_progreso). Si el filtro deja fuera una tarea en progreso, el operario
no la encuentra: el filtro es la puerta de entrada a la tarea.
"""

import pytest

from tests.conftest import nueva_tarea


@pytest.fixture
def tareas(preparar_escenario):
    c = preparar_escenario.cliente("operario")
    pendiente = nueva_tarea(c, titulo="Limpiar tolva", descripcion="Línea 2")
    en_progreso = nueva_tarea(c, titulo="Cambiar molde 7")
    c.put(f"/api/tareas/{en_progreso['id']}", json={"estado": "en_progreso", "version": 1})
    completada = nueva_tarea(c, titulo="Revisar molde 3")
    c.post(f"/api/tareas/{completada['id']}/completar")
    return c


def _titulos(cliente, consulta=""):
    r = cliente.get(f"/api/tareas{consulta}")
    assert r.status_code == 200
    return sorted(t["titulo"] for t in r.get_json())


def test_sin_filtros_devuelve_todo(tareas):
    assert _titulos(tareas) == ["Cambiar molde 7", "Limpiar tolva", "Revisar molde 3"]


def test_pendientes_incluye_las_que_estan_en_progreso(tareas):
    assert _titulos(tareas, "?estado=pendientes") == ["Cambiar molde 7", "Limpiar tolva"]


def test_estado_exacto(tareas):
    assert _titulos(tareas, "?estado=completada") == ["Revisar molde 3"]
    assert _titulos(tareas, "?estado=en_progreso") == ["Cambiar molde 7"]


def test_busqueda_ignora_mayusculas_y_mira_la_descripcion(tareas):
    assert _titulos(tareas, "?q=MOLDE") == ["Cambiar molde 7", "Revisar molde 3"]
    assert _titulos(tareas, "?q=línea") == ["Limpiar tolva"]


def test_estado_y_busqueda_combinados(tareas):
    assert _titulos(tareas, "?estado=pendientes&q=molde") == ["Cambiar molde 7"]
