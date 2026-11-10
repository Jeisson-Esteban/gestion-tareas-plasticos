# Resultados

> **DEF-01 fue sembrado a propósito.** En la primera versión, `estado=pendientes` devuelve
> solo las tareas `pendiente` y omite las `en_progreso`. Se dejó en un commit propio
> (`71b101e`) para demostrar el ciclo completo de un defecto: prueba roja → issue → PR con
> `Fixes #N` → verde.

## Ejecución de pruebas

| Momento | Commit | Pasan | Fallan | CI (job `rapidas`) |
|---|---|---|---|---|
| Primer push, con DEF-01 | `1c1b444` | 165 | 2 (CP-06) | ❌ [run #1](https://github.com/Jeisson-Esteban/gestion-tareas-plasticos/actions/runs/42746388580) |
| PR #11, commit con la prueba que reproduce DEF-01 | `19967bc` | 165 | 3 (CP-06) | ❌ [run #3](https://github.com/Jeisson-Esteban/gestion-tareas-plasticos/actions/runs/42748484917) |
| PR #11, commit con la corrección | `a9ceba3` | 168 | 0 | ✅ [run #4](https://github.com/Jeisson-Esteban/gestion-tareas-plasticos/actions/runs/42748706231) |
| `main` después del merge | `ce29ceb` | 168 | 0 | ✅ [run #5](https://github.com/Jeisson-Esteban/gestion-tareas-plasticos/actions/runs/42748921730) |
| Pruebas reforzadas por mutación | este PR | 178 | 0 | — |

E2E (CP-09): pasa en local con Chrome headless (1 prueba, entre 8 y 14 s), tanto levantando su
propia app como contra una app ya levantada (`E2E_URL`), que es el modo del job nocturno.

## Cobertura (`pytest -m "not e2e" --cov=app`)

| Módulo | Antes de mutación (`ce29ceb`) | Después |
|---|---|---|
| `__init__.py` | 100 % | 100 % |
| `db.py` | 92 % | 92 % |
| `permisos.py` | 95 % | 100 % |
| `rutas_api.py` | 96 % | 96 % |
| `rutas_web.py` | 30 % | 30 % (lo cubre la E2E, que no entra en esta medición) |
| `servicios.py` | 100 % | 100 % |
| **Total** | **87 %** | **87 %** (meta ≥ 80 %) |

## Pruebas de mutación (mutmut 3.8.1, WSL Ubuntu)

Se mutan `app/permisos.py` y `app/servicios.py`. mutmut exige la suite en verde, así que la
medición inicial se hizo sobre `main` ya con DEF-01 corregido.

| Medición | Pruebas | Mutantes | Eliminados | Sobrevivientes | Puntaje |
|---|---|---|---|---|---|
| Inicial (`ce29ceb`) | 168 | 210 | 170 | 40 | 81,0 % |
| Final (pruebas reforzadas) | 178 | 210 | 209 | 1 | 99,5 % |

Los 40 sobrevivientes iniciales, por tipo:

| Tipo | Cantidad | Ejemplo |
|---|---|---|
| Mensaje de error que ninguna prueba verificaba (texto con "XX", en minúsculas o en mayúsculas) | 21 | `"La fecha límite no puede ser anterior a hoy"` → `"XX…XX"` |
| Aserción débil (se comparaban claves, no valores) | 6 | `errores["email"] = error` → `None` |
| Rama o valor por defecto nunca ejercitado | 12 | 8 claves de `_fila()` (MATRIZ se arma al importar); 3 `or ""`; `if fila is None: return False` → `True` en `puede()` |
| Equivalente (no se puede matar) | 1 | `email or ""` → `email or "XXXX"`: ninguno de los dos cumple el patrón de email |

Tres mutantes que sobrevivían y la prueba que ahora los elimina:

| Mutante | Cambio | Prueba que lo elimina |
|---|---|---|
| `x_validar_registro__mutmut_8` | `errores["email"] = error` → `errores["email"] = None` | `test_validaciones.py::test_registro_reporta_cada_campo_invalido` (compara el dict completo) |
| `x_validar_fecha_limite__mutmut_8` (CP-02) | `"La fecha límite no puede ser anterior a hoy"` → `"XXLa fecha límite…XX"` | `test_validaciones.py::test_mensajes_de_error_exactos[fecha-pasada]` |
| `x_puede__mutmut_14` (CP-04) | `if fila is None: return False` → `return True` | `test_permisos.py::test_celda_faltante_en_la_matriz_se_niega` |

Conclusión: con 100 % de cobertura en `servicios.py` sobrevivían 31 mutantes de ese módulo.
Que una línea se ejecute no significa que alguna prueba verifique su resultado. La cobertura
total no cambió (87 %), pero el puntaje de mutación pasó de 81,0 % a 99,5 %.

## Defectos

| ID | Descripción | Detectado por | Issue | PR | Estado |
|---|---|---|---|---|---|
| DEF-01 | `estado=pendientes` omite las tareas `en_progreso` | CP-06 (`test_filtros.py`) | [#10](https://github.com/Jeisson-Esteban/gestion-tareas-plasticos/issues/10) | [#11](https://github.com/Jeisson-Esteban/gestion-tareas-plasticos/pull/11) | Cerrado (merge `ce29ceb`) |
