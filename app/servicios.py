"""Reglas de negocio como funciones puras (no dependen de Flask ni de la BD)."""

import re
from datetime import date

from .permisos import puede

ROLES = ("operario", "supervisor", "admin")
ESTADOS = ("pendiente", "en_progreso", "completada")
TITULO_MAX = 200
CONTRASENA_MIN = 8
_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- Validaciones ----------

def validar_titulo(titulo):
    """Devuelve un mensaje de error o None si el título es válido."""
    if not isinstance(titulo, str) or not titulo.strip():
        return "El título es obligatorio"
    if len(titulo.strip()) > TITULO_MAX:
        return f"El título admite máximo {TITULO_MAX} caracteres"
    return None


def parsear_fecha(valor):
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def validar_fecha_limite(valor, hoy):
    """'hoy' se recibe como parámetro para que la prueba controle el reloj."""
    fecha = parsear_fecha(valor)
    if fecha is None:
        return "Fecha inválida, use el formato AAAA-MM-DD"
    if fecha < hoy:
        return "La fecha límite no puede ser anterior a hoy"
    return None


def validar_contrasena(contrasena):
    if not isinstance(contrasena, str) or len(contrasena) < CONTRASENA_MIN:
        return f"La contraseña debe tener al menos {CONTRASENA_MIN} caracteres"
    tiene_letra = any(c.isalpha() for c in contrasena)
    tiene_numero = any(c.isdigit() for c in contrasena)
    if not (tiene_letra and tiene_numero):
        return "La contraseña debe tener al menos una letra y un número"
    return None


def normalizar_email(email):
    return (email or "").strip().lower()


def validar_email(email):
    if not _PATRON_EMAIL.match(email or ""):
        return "Email inválido"
    return None


def validar_registro(datos):
    """Devuelve un dict {campo: error}. Vacío significa válido.

    El email duplicado no se valida aquí: lo detecta la restricción UNIQUE.
    """
    errores = {}
    error = validar_email(normalizar_email(datos.get("email")))
    if error:
        errores["email"] = error
    error = validar_contrasena(datos.get("contrasena"))
    if error:
        errores["contrasena"] = error
    if not (datos.get("nombre") or "").strip():
        errores["nombre"] = "El nombre es obligatorio"
    return errores


def validar_tarea_nueva(datos, hoy):
    errores = {}
    error = validar_titulo(datos.get("titulo"))
    if error:
        errores["titulo"] = error
    error = validar_fecha_limite(datos.get("fecha_limite"), hoy)
    if error:
        errores["fecha_limite"] = error
    try:
        int(datos.get("asignado_id"))
    except (TypeError, ValueError):
        errores["asignado_id"] = "Debe indicar un usuario asignado válido"
    return errores


# ---------- Transiciones de estado ----------

TRANSICIONES = {
    ("pendiente", "en_progreso"),
    ("en_progreso", "completada"),
    ("pendiente", "completada"),
}

# Transiciones que solo se permiten a través de una acción explícita.
TRANSICIONES_POR_ACCION = {
    "reabrir": {("completada", "pendiente")},
}


def puede_transicionar(desde, hacia, accion=None):
    if accion is None:
        return (desde, hacia) in TRANSICIONES
    return (desde, hacia) in TRANSICIONES_POR_ACCION.get(accion, set())


def puede_reabrir(rol, relacion):
    """Solo el creador de la tarea o un admin pueden reabrirla."""
    return rol == "admin" or relacion == "creada"


def puede_reasignar(estado):
    """Una tarea completada no se reasigna: primero hay que reabrirla."""
    return estado != "completada"


# ---------- Relación usuario-tarea, visibilidad y filtros ----------

def relacion_con(usuario_id, tarea):
    if tarea["creador_id"] == usuario_id:
        return "creada"
    if tarea["asignado_id"] == usuario_id:
        return "asignada"
    return "ajena"


def tareas_visibles(usuario, tareas):
    return [
        t for t in tareas
        if puede(usuario["rol"], relacion_con(usuario["id"], t), "ver")
    ]


def filtrar_tareas(tareas, estado=None, q=None):
    resultado = list(tareas)
    if estado == "pendientes":
        # "pendientes" = todo lo que todavía no está completado
        resultado = [t for t in resultado if t["estado"] == "pendiente"]
    elif estado:
        resultado = [t for t in resultado if t["estado"] == estado]
    if q and q.strip():
        texto = q.strip().lower()
        resultado = [
            t for t in resultado
            if texto in t["titulo"].lower() or texto in (t["descripcion"] or "").lower()
        ]
    return resultado
