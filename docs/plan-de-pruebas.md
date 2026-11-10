# Plan de pruebas

## Objetivo

Verificar las reglas de negocio de la app de gestión de tareas (validaciones, estados,
permisos, concurrencia y filtros) en tres niveles, con trazabilidad requisito → prueba → issue.

## Estrategia

| Nivel | Qué prueba | Herramienta | Cuándo corre |
|---|---|---|---|
| Unitaria | `servicios.py` y `permisos.py`: funciones puras, sin Flask | pytest | En cada push/PR (job `rapidas`) |
| Integración | API por HTTP con SQLite temporal y usuarios reales | pytest + cliente de Flask | En cada push/PR (job `rapidas`) |
| E2E | Flujo completo en el navegador | Selenium + Chrome headless | Después de `rapidas` (job `e2e`) |
| Mutación | Calidad de las pruebas sobre `permisos.py` y `servicios.py` | mutmut | Semanal o a mano (job `mutacion`) |

Criterios de salida: todas las pruebas en verde, cobertura de `app/` ≥ 80 % y el puntaje de
mutación registrado antes y después de reforzar las pruebas.

## Casos de prueba

| ID | Archivo | Qué cubre | Técnica |
|---|---|---|---|
| CP-01 | `unit/test_validaciones.py` | Título (0, 1, 200, 201, espacios), fecha (ayer, hoy, mañana), contraseña (7, 8) | Valores límite |
| CP-02 | `unit/test_transiciones.py` | Los 9 pares de estados, reabrir y reasignar | Transición de estados |
| CP-03 | `unit/test_permisos.py` | `puede()` contra las 36 celdas de la matriz | Tabla de decisión |
| CP-04 | `integracion/test_autorizacion_api.py` | La misma matriz por HTTP; 401 sin sesión; registro y login | Tabla de decisión |
| CP-05 | `integracion/test_filtros.py` | Estado + búsqueda combinados | Integración |
| CP-06 | `integracion/test_concurrencia.py` | Dos lecturas de la versión 1; la segunda escritura recibe 409 | Integración |
| CP-07 | `integracion/test_perfil.py` | Cambio de contraseña; la anterior deja de servir | Integración |
| CP-08 | `e2e/test_flujo_supervisor.py` | El supervisor crea y asigna; el operario completa | E2E |
| CP-09 | `pyproject.toml` (`[tool.mutmut]`) | Mutantes eliminados en permisos y servicios | Mutación |

## Decisiones de diseño que facilitan las pruebas

- **Lógica en funciones puras.** `servicios.py` no importa Flask y recibe `hoy` como parámetro,
  así que las pruebas de fecha no dependen del reloj.
- **La matriz es requisito y prueba a la vez.** `MATRIZ` (en `permisos.py`) la lee `puede()`, y
  `casos_matriz()` la recorre para generar los 36 casos unitarios y los 36 de integración.
- **SQLite temporal por prueba.** `create_app({"DATABASE": tmp_path/...})` aísla cada caso.
- **Bloqueo optimista en una sola sentencia.** `UPDATE ... WHERE id = ? AND version = ?`: si no
  actualiza ninguna fila, hubo conflicto (409).
- **Selectores `data-testid`.** Selenium no depende de clases CSS ni de textos, y eso reduce la
  fragilidad de la prueba E2E.

## Defecto sembrado (DEF-01)

`estado=pendientes` debería devolver las tareas `pendiente` y `en_progreso`, pero devuelve solo
`pendiente` (`servicios.filtrar_tareas`). Lo detectan dos pruebas de CP-05. Ciclo:
prueba roja → issue con la plantilla *Defecto* → PR con `Fixes #N` → check en verde → merge.
