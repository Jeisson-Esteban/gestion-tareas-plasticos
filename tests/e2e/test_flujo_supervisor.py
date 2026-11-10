"""CP-09 (aceptación, parte automatizada) · E2E del cambio de turno.

El supervisor crea y asigna una tarea, y el operario del turno la completa.

Los selectores usan data-testid para que un cambio de diseño (clases, textos,
estructura) no rompa la prueba: es la mitigación de la fragilidad de Selenium.

Si existe E2E_URL se prueba contra esa app ya levantada (job nocturno de CI,
sembrada con `flask --app app sembrar`). Si no, la prueba levanta su propia
app con SQLite temporal.
"""

import os
import threading
import uuid

import pytest
from werkzeug.serving import make_server

from app import create_app, db

webdriver = pytest.importorskip("selenium.webdriver")
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import Select, WebDriverWait  # noqa: E402

pytestmark = pytest.mark.e2e

# Mismos usuarios que crea `flask --app app sembrar`
CLAVE = db.CONTRASENA_DEMO
SUPERVISOR = "supervisor@planta.local"
OPERARIO = "operario@planta.local"


@pytest.fixture
def servidor(tmp_path):
    if os.environ.get("E2E_URL"):
        yield os.environ["E2E_URL"].rstrip("/")
        return

    app = create_app({
        "SECRET_KEY": "e2e",
        "DATABASE": str(tmp_path / "e2e.sqlite"),
        "HASH_METODO": "pbkdf2:sha256:1000",
    })
    assert app.test_cli_runner().invoke(args=["sembrar"]).exit_code == 0
    srv = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.fixture
def navegador():
    opciones = webdriver.ChromeOptions()
    for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,900"):
        opciones.add_argument(arg)
    try:
        driver = webdriver.Chrome(options=opciones)
    except Exception as error:  # sin Chrome en la máquina
        pytest.skip(f"Chrome no disponible: {error}")
    yield driver
    driver.quit()


def _el(driver, testid):
    return WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-testid="{testid}"]')))


def _iniciar_sesion(driver, base, email):
    driver.get(f"{base}/login")
    _el(driver, "login-email").send_keys(email)
    _el(driver, "login-contrasena").send_keys(CLAVE)
    _el(driver, "login-enviar").click()
    _el(driver, "tabla-tareas")


def _fila(driver, titulo):
    for fila in driver.find_elements(By.CSS_SELECTOR, '[data-testid="tarea"]'):
        if fila.find_element(By.CSS_SELECTOR, '[data-testid="tarea-titulo"]').text == titulo:
            return fila
    raise AssertionError(f"No aparece la tarea {titulo!r} en el panel")


def _estado(fila):
    return fila.find_element(By.CSS_SELECTOR, '[data-testid="tarea-estado"]').text


def test_supervisor_asigna_y_operario_completa(servidor, navegador):
    base = servidor
    # título único: contra una app compartida puede haber corridas anteriores
    titulo = f"Revisar molde de tapas {uuid.uuid4().hex[:6]}"

    # 1. El supervisor crea la tarea y se la asigna al operario
    _iniciar_sesion(navegador, base, SUPERVISOR)
    _el(navegador, "crear-titulo").send_keys(titulo)
    Select(_el(navegador, "crear-asignado")).select_by_visible_text("Olga Operaria (operario)")
    _el(navegador, "crear-enviar").click()
    assert _el(navegador, "mensaje").text == "Tarea creada"
    assert _estado(_fila(navegador, titulo)) == "pendiente"
    _el(navegador, "logout").click()

    # 2. El operario la ve en su panel y la completa
    _iniciar_sesion(navegador, base, OPERARIO)
    _fila(navegador, titulo).find_element(By.CSS_SELECTOR, '[data-testid="btn-completar"]').click()
    assert _el(navegador, "mensaje").text == "Tarea completada"
    assert _estado(_fila(navegador, titulo)) == "completada"

    # 3. El filtro de completadas la muestra
    Select(_el(navegador, "filtro-estado")).select_by_value("completada")
    _el(navegador, "filtro-aplicar").click()
    assert _estado(_fila(navegador, titulo)) == "completada"
