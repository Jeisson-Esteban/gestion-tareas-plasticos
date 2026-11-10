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

| ID | Caso | Técnica | Cómo se ejecuta |
|---|---|---|---|
| CP-01 | Título: 0, 1, 200, 201 caracteres y solo espacios | Valores límite | `unit/test_validaciones.py` |
| CP-02 | Fecha límite: ayer, hoy, mañana | Valores límite | `unit/test_validaciones.py` |
| CP-03 | Contraseña: 7 y 8 caracteres, sin letra, sin número | Valores límite | `unit/test_validaciones.py`, `integracion/test_perfil.py` |
| CP-04 | Matriz de autorización (3 roles × 3 relaciones × 4 acciones) | Tabla de decisión | `unit/test_permisos.py` y la misma matriz por HTTP en `integracion/test_autorizacion_api.py` |
| CP-05 | Reabrir y reasignar una tarea completada | Transición de estados | `unit/test_transiciones.py`, `integracion/test_autorizacion_api.py` |
| CP-06 | Filtro por estado + búsqueda por texto | Integración | `integracion/test_filtros.py` |
| CP-07 | Edición simultánea: la segunda escritura recibe 409 | Integración | `integracion/test_concurrencia.py` |
| CP-08 | Usabilidad del panel en celular | Exploratoria / manual | Manual, en un teléfono o con las herramientas de desarrollo del navegador |
| CP-09 | Asignación al cambio de turno: el supervisor asigna y el operario completa | Aceptación | Parte automatizada en `e2e/test_flujo_supervisor.py`; la validación final la hace el usuario |

La calidad de las pruebas de CP-01 a CP-05 se mide además con pruebas de mutación (mutmut) sobre
`permisos.py` y `servicios.py`.

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
`pendiente` (`servicios.filtrar_tareas`). Lo detectan dos pruebas de CP-06. Ciclo:
prueba roja → issue con la plantilla *Defecto* → PR con `Fixes #N` → check en verde → merge.
