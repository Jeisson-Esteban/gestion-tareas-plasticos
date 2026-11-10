Cordial saludo, profesor Libardo y compañeros. Aquí mi ponencia de esta semana.

# Plan de pruebas manuales y automatizadas para el Sistema de Gestión de Tareas de Plásticos Sustentables

## Por qué un plan con evidencia y no solo una propuesta

Como recuerda Sommerville (2011) citando a Dijkstra, las pruebas pueden mostrar la presencia de errores, pero no su ausencia. Por eso, esta semana no me quedé en describir qué probaría: construí una versión mínima del sistema de gestión de tareas (Flask, SQLite y sesiones, con roles de operario, supervisor y administrador) y le apliqué el plan completo. Así, cada resultado que menciono salió de una ejecución real y se puede revisar en el repositorio público: https://github.com/Jeisson-Esteban/gestion-tareas-plasticos

Elegí GitHub porque reúne en un solo lugar lo que el plan necesita: *issues* con plantillas para los casos y los defectos, un tablero (Projects), *milestones* por fase y GitHub Actions para ejecutar las pruebas en cada cambio. Jira es más fuerte en la gestión de casos y reportes, pero habría que integrarlo con otra herramienta para ejecutar las pruebas; GitLab ofrece un CI integrado comparable. Esto responde en parte la pregunta del foro: la importancia práctica de automatizar depende de lo que la herramienta permita repetir y rastrear sin trabajo adicional.

## El plan de pruebas en GitHub

### Cómo decidí qué automatizar

No todo vale la pena automatizar (Chopra, 2018). La automatización de pruebas también se ha llevado a pilotos en organizaciones colombianas (Serna López et al., 2020), y este plan es un piloto a pequeña escala del mismo tipo. Para decidir qué automatizar usé una priorización en la línea de las pruebas basadas en riesgo que mapean Bastidas et al. (2021). La fórmula concreta es mía: cada caso recibe un puntaje **F + R + E − C**, donde F es la frecuencia con que hay que ejecutarlo, R el riesgo para la planta si falla, E la estabilidad del requisito y C el costo de automatizarlo, cada uno de 1 a 5. Con 9 o más, el caso va al CI en cada cambio; entre 6 y 8, se automatiza en parte y corre de noche; con 5 o menos, queda manual.

| ID | Caso | Técnica | F | R | E | C | Puntaje | Ejecución |
|---|---|---|---|---|---|---|---|---|
| CP-01 | Título (0, 1, 200, 201 caracteres, solo espacios) | Valores límite | 4 | 3 | 5 | 1 | 11 | Automatizada (CI) |
| CP-02 | Fecha límite (ayer, hoy, mañana) | Valores límite | 4 | 3 | 5 | 1 | 11 | Automatizada (CI) |
| CP-03 | Contraseña (7 y 8 caracteres, letra y número) | Valores límite | 3 | 4 | 5 | 1 | 11 | Automatizada (CI) |
| CP-04 | Matriz de autorización | Tabla de decisión | 5 | 5 | 4 | 2 | 12 | Automatizada (CI) |
| CP-05 | Reabrir o reasignar una tarea completada | Transición de estados | 3 | 4 | 4 | 2 | 9 | Automatizada (CI) |
| CP-06 | Filtro por estado + búsqueda | Integración | 5 | 5 | 4 | 2 | 12 | Automatizada (CI) |
| CP-07 | Edición simultánea | Integración | 3 | 5 | 4 | 3 | 9 | Automatizada (CI) |
| CP-08 | Usabilidad del panel en celular | Exploratoria | 4 | 3 | 2 | 5 | 4 | Manual |
| CP-09 | Asignación al cambio de turno | Aceptación | 4 | 5 | 3 | 4 | 8 | Prueba de extremo a extremo (E2E) nocturna + validación del supervisor |

Cada caso es un *issue* con la plantilla "Caso de prueba" (ID, técnica, precondición, pasos y resultado esperado), con etiquetas `tipo:*`, `severidad:*` y `modulo:*`, y *milestones* por fase (Análisis, Diseño, Desarrollo, Pruebas, Correcciones y Aceptación). El tablero tiene las columnas Por probar, En prueba, Defecto abierto, En corrección y Verificado, y el campo numérico con el puntaje, como se ve en la Figura 1.

**Figura 1**

*Tablero del proyecto con los casos CP-01 a CP-09 y el defecto DEF-01*

[Insertar Figura 1: docs/capturas/04-tablero-project.png]

### Tres niveles automatizados

Las pruebas no son una actividad suelta al final del desarrollo, sino una parte organizada del proceso de producción de software (Piattini Velthuis y Garzás Parra, 2015). Por eso el plan está repartido en niveles dentro del mismo repositorio:

- **Unitarias**: las reglas de negocio viven en funciones puras (`app/servicios.py` y `app/permisos.py`) que no dependen de Flask. La fecha de "hoy" entra como parámetro, así CP-02 no depende del reloj.
- **Integración**: la API se prueba por HTTP con usuarios reales y una base SQLite temporal por prueba.
- **E2E**: Selenium con Chrome *headless* recorre el flujo del cambio de turno (CP-09). Como toda automatización con Selenium, exige instalar y configurar el navegador y su *driver* (Palani, 2019); en GitHub Actions eso lo resuelve Selenium Manager. Los selectores usan atributos `data-testid`, para que un cambio de diseño no rompa la prueba.

La pieza central es la matriz de permisos de CP-04. Es una estructura de datos que la aplicación lee para decidir y que las pruebas recorren para generar sus casos; la tabla es requisito y prueba a la vez:

```python
MATRIZ = {
    "operario": {
        "creada": _fila(True, True, True, True),
        "asignada": _fila(True, False, True, False),
        "ajena": _fila(False, False, False, False),
    },
    "supervisor": {
        "creada": _fila(True, True, True, True),
        "asignada": _fila(True, False, True, False),
        "ajena": _fila(True, False, False, False),
    },
    "admin": {
        "cualquiera": _fila(True, True, True, True),
    },
}
```

```python
@pytest.mark.parametrize("rol, relacion, accion, permitido", list(casos_matriz()))
def test_puede_coincide_con_la_matriz(rol, relacion, accion, permitido):
    assert puede(rol, relacion, accion) is permitido
```

Las 36 combinaciones (3 roles × 3 relaciones × 4 acciones) se verifican dos veces: contra la función y por HTTP, es decir, 72 pruebas que salen de la misma tabla.

### Integración continua

GitHub Actions corre las pruebas unitarias y de integración en cada *pull request* y en cada *push* a `main`, con un umbral de cobertura del 80 %:

```yaml
      - run: pytest -m "not e2e" --cov=app --cov-report=term-missing --cov-fail-under=80
```

La rama `main` está protegida: exige *pull request* y que ese *check*, llamado `rapidas`, esté en verde. La regla no se aplica a los administradores; en un equipo real habría que activarla también para ellos. El E2E corre de noche y la mutación, cada semana:

```yaml
  schedule:
    - cron: "0 7 * * *"   # e2e nocturno: 2:00 a. m. hora de Colombia
    - cron: "0 6 * * 1"   # mutación semanal: lunes 1:00 a. m. hora de Colombia
```

## El ciclo completo de un defecto

Para demostrar el ciclo dejé un defecto sembrado a propósito, en un *commit* propio: el filtro "pendientes" devolvía solo las tareas en estado `pendiente` y omitía las que estaban `en_progreso`. En el primer *push*, CP-06 lo detectó y el CI quedó en rojo: 165 pruebas pasaron y 2 fallaron (Figura 2).

**Figura 2**

*Primer push: el job `rapidas` falla por las dos pruebas de CP-06*

[Insertar Figura 2: docs/capturas/00-ci-rojo-def01.png]

Lo reporté como el *issue* #10 con la plantilla "Defecto", severidad alta y la referencia al caso que lo detectó, CP-06 (Figura 3).

**Figura 3**

*Issue DEF-01 con la plantilla de defecto, sus etiquetas y el milestone Correcciones*

[Insertar Figura 3: docs/capturas/05-issue-defecto.png]

Con `main` ya protegida, la corrección fue el *pull request* #11, en dos *commits*. El primero solo agrega una prueba unitaria que reproduce el defecto, y el CI la marcó en rojo, así que el PR no se podía fusionar (Figura 4). El segundo corrige `filtrar_tareas`, y el CI pasó a verde con 168 pruebas. Como el PR dice `Fixes #10`, al hacer el *merge* el *issue* se cerró solo (Figura 5). Después del *merge*, `main` quedó en verde (Figura 6).

**Figura 4**

*Ejecución del PR #11 con la prueba que reproduce el defecto: `rapidas` en rojo*

[Insertar Figura 4: docs/capturas/02-pr-bloqueado.png]

**Figura 5**

*PR #11 con "Fixes #10": el primer commit en rojo y el segundo en verde*

[Insertar Figura 5: docs/capturas/03-pr-verde-fixes.png]

**Figura 6**

*Historial de GitHub Actions: del rojo inicial al verde después del merge*

[Insertar Figura 6: docs/capturas/01-actions-verde.png]

## La cobertura no basta: pruebas de mutación

Con las pruebas unitarias y de integración (sin la E2E), la cobertura de `app/` fue de 87 %. El módulo `servicios.py` llegó al 100 %, y `rutas_web.py` se quedó en 30 % porque esas vistas solo las recorre la E2E (Figura 7). Parecía suficiente, así que medí la calidad de las pruebas con mutmut: la herramienta introduce pequeños cambios en el código (mutantes) y revisa si alguna prueba falla.

**Figura 7**

*Reporte de cobertura local: 87 % total y 100 % en `servicios.py`*

[Insertar Figura 7: docs/capturas/06-cobertura.png]

El resultado inicial fue de 210 mutantes, 170 eliminados y 40 sobrevivientes: 81,0 %. De esos 40, 31 eran de `servicios.py`, un módulo con 100 % de cobertura. Al revisarlos encontré que 39 se debían a tres problemas en mis pruebas (21 mensajes de error que ninguna prueba verificaba, 6 aserciones débiles que comparaban las claves de un diccionario pero no sus valores, y 12 ramas o valores por defecto que nunca se ejercitaban) y que 1 era equivalente. Tres ejemplos concretos:

- `errores["email"] = error` mutado a `errores["email"] = None` sobrevivía porque la prueba solo miraba las claves. Ahora lo elimina `test_registro_reporta_cada_campo_invalido`, que compara el diccionario completo.
- En CP-02, el mensaje "La fecha límite no puede ser anterior a hoy" mutado a "XX…XX" sobrevivía. Ahora lo elimina `test_mensajes_de_error_exactos[fecha-pasada]`.
- En CP-04, la regla de fallar cerrado de `puede()` (`if fila is None: return False`) mutada a `return True` sobrevivía porque ninguna entrada llegaba a esa rama. Ahora lo elimina `test_celda_faltante_en_la_matriz_se_niega`.

Sin cambiar ni una línea de la aplicación, con aserciones más estrictas y diez pruebas nuevas (de 168 a 178), el resultado fue de 209 eliminados y 1 sobreviviente: 99,5 % (Figura 8). El que queda es equivalente: cambia `email or ""` por `email or "XXXX"`, y ninguno de los dos valores es un email válido, así que ninguna prueba puede distinguirlos. El job de mutación en GitHub Actions dio los mismos sobrevivientes en las dos mediciones (40 y 1), así que el resultado no depende de mi equipo. La cobertura siguió en 87 %; lo que mejoró fue la capacidad de las pruebas para detectar errores.

**Figura 8**

*Resumen de mutmut antes y después de reforzar las pruebas: de 81,0 % a 99,5 %*

[Insertar Figura 8: docs/capturas/07-mutacion.png]

## Lo que sigue siendo manual

Aquí se ve la diferencia entre verificar y validar (Echeverri et al., 2013): el CI verifica que el sistema cumple sus reglas, pero solo las personas que lo usan pueden validar que sirve. CP-08 (uso del panel en celular) es manual a propósito, porque que algo "se vea bien y se pueda pulsar con el dedo" lo juzga una persona; para prepararlo agregué a las vistas la etiqueta `viewport` y una tabla desplazable. La planificación de pruebas también puede apoyarse en enfoques centrados en el usuario como *design thinking* (Pérez Vera et al., 2020), y eso se nota en CP-08 y CP-09, que parten de cómo trabaja el operario. CP-09 tiene una parte automatizada, la E2E que se ve en la Figura 9, pero la aceptación final la da el supervisor en un cambio de turno real.

**Figura 9**

*Panel del operario capturado por la prueba E2E justo después de completar la tarea*

[Insertar Figura 9: docs/capturas/08-panel-app.png]

## Ventajas y desventajas del plan

**Ventajas**

- **Detecta antes de que llegue a planta.** El CI marcó el defecto del filtro en el primer *push*, y desde que `main` quedó protegida ningún cambio entra sin el *check* `rapidas` en verde: el PR #11 no se pudo fusionar mientras la prueba estuvo en rojo.
- **Trazabilidad completa.** Del caso CP-06 al *issue* #10, al PR #11 y al *commit* que lo corrige, todo enlazado en GitHub.
- **Rápido.** En GitHub Actions, el job `rapidas` tarda menos de 30 segundos y el de mutación, menos de un minuto, así que no frenan el trabajo.
- **Requisito y prueba en la misma tabla.** Si cambia una regla de permisos, cambia la matriz y las 72 pruebas que salen de ella se ajustan solas.

**Desventajas**

- **El E2E es frágil, y lo comprobé.** En mi equipo pasaba siempre, pero la primera vez que corrió en GitHub Actions falló con "stale element reference": después de pulsar "Filtrar", la prueba buscaba las filas en la página vieja, antes de que terminara la recarga. La aplicación no tenía ningún error; el problema era la prueba. Lo corregí haciendo que cada clic espere a que la página anterior desaparezca, y desde entonces pasa también en CI. Por eso el E2E corre de noche y no en cada PR, aunque eso implica que un error de interfaz puede tardar hasta un día en verse.
- **El E2E no reemplaza el celular real del operario.** Selenium corre en un Chrome de escritorio; CP-08 sigue dependiendo de que alguien pruebe el panel en un teléfono de la planta.
- **La aceptación depende de la disponibilidad del supervisor.** CP-09 solo se cierra en un cambio de turno real, y eso no se puede programar como un job.
- **SQLite no es la base de producción.** Las pruebas de integración usan SQLite temporal; un error propio del motor real no se detectaría.
- **Mantener la suite tiene costo.** Cada cambio de regla, como un rol nuevo, obliga a revisar la matriz y las pruebas. Además, la herramienta mutmut no corre en Windows nativo: tuve que usar WSL y armar el entorno virtual a mano.

## Diálogo con los compañeros

**Alexis.** En nuestro intercambio sostuve que el filtro es la puerta de entrada a la tarea. Ahora lo puedo respaldar con evidencia: DEF-01 no rompía ninguna tarea, pero escondía las que estaban en progreso, justo las que el operario tiene a medias. Para el usuario, una tarea que no aparece en el filtro es una tarea que no existe. Aun así, me pregunto si el filtro debe pesar lo mismo que la matriz de permisos: un filtro mal hecho oculta una tarea, pero un permiso mal hecho deja que alguien borre una tarea ajena. Con mi fórmula ambos quedan en 12 porque R no distingue entre riesgo operativo y riesgo de seguridad. ¿Tú los separarías?

**Yeison.** Le planteé que la cobertura, por sí sola, no dice si las pruebas sirven. El antes y después de mutación lo muestra: con 87 % de cobertura (y 100 % en `servicios.py`) sobrevivían 40 mutantes, y el puntaje pasó de 81,0 % a 99,5 % sin tocar la aplicación. Pero tengo que reconocer el límite de mi propio argumento: la mutación tampoco es gratis. Exige la suite en verde, no corre en Windows nativo y deja mutantes equivalentes que alguien tiene que revisar a mano. Por eso en el CI la dejé semanal y sin bloquear (`mutmut run || true`): el puntaje informa, no frena.

**[COMPLETAR: nombre del compañero de la edición simultánea].** CP-07 cubre su preocupación con bloqueo optimista: cada tarea tiene un número de versión y la escritura usa un solo `UPDATE ... WHERE id = ? AND version = ?`. En la prueba, el supervisor y el administrador leen la versión 1, el primero guarda y el segundo recibe un error 409 (conflicto) en vez de pisar el cambio en silencio. Sin embargo, el bloqueo evita la pérdida de datos pero traslada el problema al segundo usuario: la API le responde 409 y mi plan todavía no prueba qué ve en pantalla ni cómo recupera su trabajo. Ese sería un caso nuevo, probablemente manual.

**Ian.** [COMPLETAR: el punto de Ian y cómo lo conecta el plan.]

**Naren.** [COMPLETAR: el punto de Naren y cómo lo conecta el plan.]

## Conclusión

Las pruebas manuales y las automatizadas no compiten. Las manuales siguen siendo necesarias donde decide el criterio humano, como la usabilidad y la aceptación; la automatización es importante porque las herramientas disponibles permiten repetirla en cada cambio sin costo adicional. El puntaje F + R + E − C me ayudó a dejar en el CI lo repetitivo y de alto riesgo, y en manos de una persona lo que depende del juicio humano. La lección más valiosa fue que tener el código en verde y con buena cobertura no garantiza buenas pruebas: hizo falta un defecto sembrado para comprobar que el CI lo detectaba, y pruebas de mutación para descubrir que 39 cambios reales en el código pasaban sin que ninguna prueba lo notara. Como siguiente paso, la automatización apoyada en inteligencia artificial (Smith et al., 2022) podría ayudar a reducir el mantenimiento de pruebas frágiles como la E2E.

## Referencias

Bastidas, M. I., Pardo, C. J. y Ardila, C. A. (2021). A systematic literature mapping: Risk-based testing in software development. *Ingeniería y Competitividad, 23*(1), 2-18.

Chopra, R. (2018). Test management and automation. En *Software quality assurance: A self-teaching introduction* (pp. 371-395). Mercury Learning & Information.

Echeverri, J. et al. (2013). Verificación y validación. En *Reflexiones sobre ingeniería de requisitos y pruebas de software* (pp. 64-75). Corporación Universitaria Remington.

Palani, N. (2019). Tools installation. En *Advanced selenium web accessibility testing: Software automation testing secrets revealed* (pp. 29-33). Momentum Press.

Pérez Vera, Y. et al. (2020). Design thinking en la planificación de pruebas de software. *Innovación y Software, 1*(2), 40-51.

Piattini Velthuis, M. G. y Garzás Parra, J. (2015). Las pruebas de software. En *Fábricas de software: experiencias, tecnologías y organización* (pp. 272-277). RA-MA Editorial.

Serna López, G. A. et al. (2020). Piloto de automatización de pruebas de software en la Unidad de Servicios Tecnológicos del Centro de Servicios y Gestión Empresarial (CESGE) del SENA. *Revista CINTEX, 25*(2), 45-50.

Smith, A. L. et al. (2022). AI-based test automation. En *Artificial intelligence and software testing: Building systems you can trust* (pp. 104-125). BCS Learning & Development Limited.

Sommerville, I. (2011). Pruebas de software. En *Ingeniería de software* (pp. 237-250). Pearson Educación.

## Notas para publicar

Esta sección no va en el foro; el generador del Word la omite automáticamente.

| Marcador | Archivo | Estado |
|---|---|---|
| Figura 1 | `docs/capturas/04-tablero-project.png` | **Pendiente**: tómala tú o haz público el tablero (ver `docs/capturas/PENDIENTES.md`). Si no la tienes, borra la Figura 1 y la frase que la cita |
| Figura 2 | `docs/capturas/00-ci-rojo-def01.png` | Lista (la tomaste tú) |
| Figura 3 | `docs/capturas/05-issue-defecto.png` | Lista |
| Figura 4 | `docs/capturas/02-pr-bloqueado.png` | Lista |
| Figura 5 | `docs/capturas/03-pr-verde-fixes.png` | Lista |
| Figura 6 | `docs/capturas/01-actions-verde.png` | Lista |
| Figura 7 | `docs/capturas/06-cobertura.png` | Lista |
| Figura 8 | `docs/capturas/07-mutacion.png` | Lista |
| Figura 9 | `docs/capturas/08-panel-app.png` | Lista |

Para verificar antes de publicar:

1. **Los tres marcadores [COMPLETAR]**: el nombre del compañero de la edición simultánea y los puntos de Ian y Naren. No tengo lo que plantearon y no lo inventé. Si no hay nada que agregar, borra esos párrafos.
2. **Alexis y Yeison**: confirma que los párrafos reflejan lo que de verdad se discutió.
3. **Sommerville y Dijkstra**: verifica que la frase sobre la presencia y la ausencia de errores aparezca en las páginas 237-250. Si no está, cámbiala por: "Sommerville (2011) presenta las pruebas como el proceso para mostrar que un programa hace lo que debe y para descubrir defectos antes de su uso."
4. **Recursos complementarios** (Echeverri, Palani, Pérez Vera, Serna López, Smith): se citan con afirmaciones generales basadas en el tema de cada recurso. Revisa que coincidan con tu lectura. Corregí dos erratas de la guía: "AI-based" (la guía dice "Al-based") y "Tools installation" (la guía dice "Tools installación").
5. **Puntaje F + R + E − C**: la definición y los valores son míos. Si en semanas anteriores usaste otra, ajústala aquí y en el tablero.
6. **El caso (Anexo II)**: no tuve el documento. La ponencia solo usa lo que está implementado (roles, estados, cambio de turno, celular del operario). Confirma que coincide con el anexo.
7. **178 pruebas y 99,5 %**: quedan en `main` cuando se fusione el PR con las pruebas reforzadas. Fusiónalo antes de publicar.
