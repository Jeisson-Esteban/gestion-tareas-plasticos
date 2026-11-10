"""CP-07 · Edición simultánea (bloqueo optimista).

Dos personas leen la misma versión y ambas guardan. Sin el control de
versión, la segunda pisaría en silencio el trabajo de la primera.
"""

from tests.conftest import nueva_tarea


def test_la_segunda_escritura_con_version_vieja_recibe_409(preparar_escenario):
    esc = preparar_escenario
    tarea = nueva_tarea(esc.cliente("supervisor"))
    url = f"/api/tareas/{tarea['id']}"
    supervisor, admin = esc.cliente("supervisor"), esc.cliente("admin")

    # Ambos leen la versión 1
    v_supervisor = supervisor.get(url).get_json()["version"]
    v_admin = admin.get(url).get_json()["version"]
    assert v_supervisor == v_admin == 1

    primera = supervisor.put(url, json={"titulo": "Versión del supervisor", "version": v_supervisor})
    assert primera.status_code == 200
    assert primera.get_json()["version"] == 2

    segunda = admin.put(url, json={"titulo": "Versión del admin", "version": v_admin})
    assert segunda.status_code == 409

    # Se conserva lo que guardó el primero
    assert supervisor.get(url).get_json()["titulo"] == "Versión del supervisor"


def test_con_la_version_actual_si_guarda(preparar_escenario):
    c = preparar_escenario.cliente("operario")
    tarea = nueva_tarea(c)
    url = f"/api/tareas/{tarea['id']}"
    c.put(url, json={"titulo": "Primera", "version": 1})
    r = c.put(url, json={"titulo": "Segunda", "version": 2})
    assert r.status_code == 200
    assert r.get_json()["version"] == 3


def test_put_sin_version_da_400(preparar_escenario):
    c = preparar_escenario.cliente("operario")
    tarea = nueva_tarea(c)
    assert c.put(f"/api/tareas/{tarea['id']}", json={"titulo": "Sin versión"}).status_code == 400


def test_put_con_datos_invalidos_no_cambia_la_version(preparar_escenario):
    c = preparar_escenario.cliente("operario")
    tarea = nueva_tarea(c)
    url = f"/api/tareas/{tarea['id']}"
    r = c.put(url, json={"titulo": "   ", "fecha_limite": "2000-01-01", "version": 1})
    assert r.status_code == 400
    assert c.get(url).get_json()["version"] == 1
