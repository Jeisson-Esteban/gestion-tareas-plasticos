"""CP-04 · Tabla de decisión (nivel integración).

La misma MATRIZ de app/permisos.py, ahora por HTTP con usuarios reales y
SQLite temporal. Si la unitaria (test_permisos.py) pasa y esta falla, el error está en
cómo la API calcula la relación o aplica el permiso, no en la tabla.
"""

import pytest

from app.permisos import casos_matriz
from tests.conftest import CLAVE, USUARIOS, nueva_tarea

CODIGO_EXITO = {"ver": 200, "editar": 200, "completar": 200, "eliminar": 204}


def _ejecutar(cliente, accion, tarea):
    url = f"/api/tareas/{tarea['id']}"
    if accion == "ver":
        return cliente.get(url)
    if accion == "editar":
        return cliente.put(url, json={"titulo": "Editada", "version": tarea["version"]})
    if accion == "completar":
        return cliente.post(f"{url}/completar")
    return cliente.delete(url)


@pytest.mark.parametrize("rol, relacion, accion, permitido", list(casos_matriz()))
def test_matriz_por_http(preparar_escenario, rol, relacion, accion, permitido):
    cliente, tarea = preparar_escenario(rol, relacion)
    respuesta = _ejecutar(cliente, accion, tarea)
    assert respuesta.status_code == (CODIGO_EXITO[accion] if permitido else 403)


def test_listado_solo_muestra_lo_que_el_usuario_puede_ver(preparar_escenario):
    esc = preparar_escenario
    ajena = nueva_tarea(esc.cliente("otro"), titulo="Ajena", asignado_id=esc.ids["otro"])

    ids_operario = [t["id"] for t in esc.cliente("operario").get("/api/tareas").get_json()]
    ids_supervisor = [t["id"] for t in esc.cliente("supervisor").get("/api/tareas").get_json()]

    assert ajena["id"] not in ids_operario
    assert ajena["id"] in ids_supervisor


def test_tarea_inexistente_da_404(preparar_escenario):
    assert preparar_escenario.cliente("admin").get("/api/tareas/999").status_code == 404


@pytest.mark.parametrize("metodo, url", [
    ("post", "/api/logout"),
    ("get", "/api/tareas"),
    ("post", "/api/tareas"),
    ("get", "/api/tareas/1"),
    ("put", "/api/tareas/1"),
    ("post", "/api/tareas/1/completar"),
    ("post", "/api/tareas/1/reabrir"),
    ("delete", "/api/tareas/1"),
    ("put", "/api/perfil/contrasena"),
])
def test_sin_sesion_todo_responde_401(cliente, metodo, url):
    assert getattr(cliente, metodo)(url, json={}).status_code == 401


# ---------- Registro y login ----------

def test_registro_exitoso_crea_operario(cliente):
    r = cliente.post("/api/registro", json={
        "email": "nueva@planta.test", "contrasena": "abcd1234", "nombre": "Nueva"})
    assert r.status_code == 201
    assert r.get_json()["rol"] == "operario"


def test_registro_invalido_da_400(cliente):
    r = cliente.post("/api/registro", json={"email": "x", "contrasena": "abc", "nombre": ""})
    assert r.status_code == 400


def test_registro_con_email_duplicado_da_409(preparar_escenario, cliente):
    r = cliente.post("/api/registro", json={
        "email": USUARIOS["operario"][0].upper(), "contrasena": "abcd1234", "nombre": "Copia"})
    assert r.status_code == 409


def test_login_falla_con_el_mismo_mensaje(preparar_escenario, cliente):
    email_mal = cliente.post("/api/login", json={"email": "nadie@planta.test", "contrasena": CLAVE})
    clave_mal = cliente.post("/api/login", json={"email": USUARIOS["operario"][0], "contrasena": "x"})
    assert email_mal.status_code == clave_mal.status_code == 401
    assert email_mal.get_json() == clave_mal.get_json()


def test_logout_cierra_la_sesion(preparar_escenario):
    c = preparar_escenario.cliente("operario")
    assert c.post("/api/logout").status_code == 200
    assert c.get("/api/tareas").status_code == 401


# ---------- CP-05: reabrir y reasignar, vistos desde la API ----------

def test_reabrir_solo_creador_o_admin(preparar_escenario):
    esc = preparar_escenario
    tarea = nueva_tarea(esc.cliente("supervisor"), asignado_id=esc.ids["operario"])
    esc.cliente("operario").post(f"/api/tareas/{tarea['id']}/completar")

    assert esc.cliente("operario").post(f"/api/tareas/{tarea['id']}/reabrir").status_code == 403
    r = esc.cliente("supervisor").post(f"/api/tareas/{tarea['id']}/reabrir")
    assert r.status_code == 200
    assert r.get_json()["estado"] == "pendiente"


def test_no_se_reabre_una_tarea_no_completada(preparar_escenario):
    c = preparar_escenario.cliente("admin")
    tarea = nueva_tarea(c)
    assert c.post(f"/api/tareas/{tarea['id']}/reabrir").status_code == 400


def test_no_se_completa_dos_veces(preparar_escenario):
    c = preparar_escenario.cliente("operario")
    tarea = nueva_tarea(c)
    assert c.post(f"/api/tareas/{tarea['id']}/completar").status_code == 200
    assert c.post(f"/api/tareas/{tarea['id']}/completar").status_code == 400


def test_no_se_reasigna_una_tarea_completada(preparar_escenario):
    esc = preparar_escenario
    c = esc.cliente("supervisor")
    tarea = nueva_tarea(c)
    completada = c.post(f"/api/tareas/{tarea['id']}/completar").get_json()
    r = c.put(f"/api/tareas/{tarea['id']}", json={
        "asignado_id": esc.ids["operario"], "version": completada["version"]})
    assert r.status_code == 400
    assert "asignado_id" in r.get_json()["detalles"]


def test_put_rechaza_transicion_invalida(preparar_escenario):
    c = preparar_escenario.cliente("operario")
    tarea = nueva_tarea(c)
    completada = c.post(f"/api/tareas/{tarea['id']}/completar").get_json()
    r = c.put(f"/api/tareas/{tarea['id']}", json={"estado": "pendiente", "version": completada["version"]})
    assert r.status_code == 400


def test_crear_con_asignado_inexistente_da_400(preparar_escenario):
    r = preparar_escenario.cliente("operario").post("/api/tareas", json={
        "titulo": "X", "fecha_limite": "2999-01-01", "asignado_id": 999})
    assert r.status_code == 400
