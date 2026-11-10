"""Matriz de permisos.

La tabla es requisito y prueba a la vez: puede() la lee para decidir y las
pruebas (unitarias y de integración) la recorren para generar sus casos.
"""

ACCIONES = ("ver", "editar", "completar", "eliminar")
RELACIONES = ("creada", "asignada", "ajena")


def _fila(ver, editar, completar, eliminar):
    return {"ver": ver, "editar": editar, "completar": completar, "eliminar": eliminar}


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


def puede(rol, relacion, accion):
    """True si el rol, con esa relación con la tarea, puede hacer la acción."""
    filas = MATRIZ.get(rol)
    if filas is None or relacion not in RELACIONES:
        return False
    fila = filas.get(relacion) or filas.get("cualquiera")
    if fila is None:
        return False
    return fila.get(accion, False)


def casos_matriz():
    """Expande la matriz a tuplas (rol, relacion, accion, permitido).

    'cualquiera' se abre en las tres relaciones para que las pruebas
    verifiquen cada combinación real.
    """
    for rol, filas in MATRIZ.items():
        for clave, fila in filas.items():
            relaciones = RELACIONES if clave == "cualquiera" else (clave,)
            for relacion in relaciones:
                for accion in ACCIONES:
                    yield rol, relacion, accion, fila[accion]
