# Resultados

> **DEF-01 fue sembrado a propósito.** En la primera versión, `estado=pendientes` devuelve
> solo las tareas `pendiente` y omite las `en_progreso`. Se dejó en un commit propio para
> demostrar el ciclo completo de un defecto: prueba roja → issue → PR con `Fixes #N` → verde.

## Ejecución de pruebas

| Fecha | Commit | Pasan | Fallan | Notas |
|---|---|---|---|---|
| 2026-11-09 | (primer push) | 165 | 2 | Fallan las dos pruebas de CP-05 por DEF-01 (esperado) |
| | (PR de la corrección) | | | |

E2E (CP-08): pasa en local con Chrome headless (1 prueba, ~14 s).

## Cobertura (`pytest -m "not e2e" --cov=app`)

| Módulo | Cobertura |
|---|---|
| `__init__.py` | 100 % |
| `db.py` | 92 % |
| `permisos.py` | 95 % |
| `rutas_api.py` | 96 % |
| `rutas_web.py` | 30 % (lo cubre la E2E, que no entra en esta medición) |
| `servicios.py` | 100 % |
| **Total** | **87 %** (meta ≥ 80 %) |

## Pruebas de mutación (mutmut 3.8.1, WSL)

| Medición | Mutantes | Eliminados | Sobrevivientes | Puntaje |
|---|---|---|---|---|
| Inicial | 210 | 170 | 40 | 81 % |
| Final | | | | |

La medición inicial se hizo con DEF-01 ya corregido, porque mutmut exige que la suite esté en verde.

Tipos de sobrevivientes en la medición inicial:

1. **Mensajes de error sin verificar** (`"El título es obligatorio"` → `"XX...XX"`). Las pruebas
   solo miran si hay error, no cuál es.
2. **Aserciones débiles**: `errores["email"] = error` → `None` sobrevive porque la prueba
   compara solo las claves del dict, no los valores.
3. **Código que nunca se ejecuta**: en `puede()`, `if fila is None: return False` → `True` sobrevive;
   ninguna entrada válida llega a esa rama.
4. **No eliminables**: los mutantes de `_fila()` se aplican al llamar la función, pero `MATRIZ`
   se construye al importar el módulo, antes de que se active el mutante.

Conclusión para la ponencia: con 100 % de cobertura en `servicios.py` sobrevivieron mutantes.
Que una línea se ejecute no significa que alguna prueba verifique su resultado.

## Defectos

| ID | Descripción | Detectado por | Issue | PR | Estado |
|---|---|---|---|---|---|
| DEF-01 | `estado=pendientes` omite las tareas `en_progreso` | CP-05 (`test_filtros.py`) | #? | #? | Abierto |
