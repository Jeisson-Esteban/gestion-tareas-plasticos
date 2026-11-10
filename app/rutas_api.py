"""API JSON. Toda la lógica de negocio vive en servicios.py y permisos.py."""

import sqlite3
from datetime import date

from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash

from . import db, servicios
from .permisos import puede

bp = Blueprint("api", __name__, url_prefix="/api")

RUTAS_PUBLICAS = {"api.registro", "api.login"}
MENSAJE_LOGIN_FALLIDO = "Email o contraseña incorrectos"


class ErrorApi(Exception):
    def __init__(self, codigo, mensaje, detalles=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = detalles


@bp.errorhandler(ErrorApi)
def _responder_error(error):
    cuerpo = {"error": error.mensaje}
    if error.detalles:
        cuerpo["detalles"] = error.detalles
    return jsonify(cuerpo), error.codigo


@bp.before_request
def _exigir_sesion():
    if request.endpoint in RUTAS_PUBLICAS:
        return None
    g.usuario = usuario_actual()
    if g.usuario is None:
        return jsonify(error="No autenticado"), 401
    return None


# ---------- Operaciones compartidas con las vistas HTML ----------

def usuario_actual():
    usuario_id = session.get("usuario_id")
    return db.usuario_por_id(usuario_id) if usuario_id else None


def autenticar(email, contrasena):
    """Mismo resultado (None) si falla el email o la contraseña."""
    usuario = db.usuario_por_email(servicios.normalizar_email(email))
    if usuario and check_password_hash(usuario["password_hash"], contrasena or ""):
        return usuario
    return None


def obtener_tarea_autorizada(usuario, tarea_id, accion):
    tarea = db.tarea_por_id(tarea_id)
    if tarea is None:
        raise ErrorApi(404, "Tarea no encontrada")
    relacion = servicios.relacion_con(usuario["id"], tarea)
    if not puede(usuario["rol"], relacion, accion):
        raise ErrorApi(403, "No tienes permiso para esta acción")
    return tarea


def crear_tarea_para(usuario, datos):
    datos = dict(datos)
    if not datos.get("asignado_id"):
        datos["asignado_id"] = usuario["id"]
    errores = servicios.validar_tarea_nueva(datos, date.today())
    if errores:
        raise ErrorApi(400, "Datos inválidos", errores)
    asignado_id = int(datos["asignado_id"])
    if db.usuario_por_id(asignado_id) is None:
        raise ErrorApi(400, "Datos inválidos", {"asignado_id": "El usuario asignado no existe"})
    tarea_id = db.crear_tarea(
        titulo=datos["titulo"].strip(),
        descripcion=(datos.get("descripcion") or "").strip() or None,
        fecha_limite=servicios.parsear_fecha(datos["fecha_limite"]).isoformat(),
        creador_id=usuario["id"],
        asignado_id=asignado_id,
    )
    return db.tarea_por_id(tarea_id)


def completar_tarea_para(usuario, tarea_id):
    tarea = obtener_tarea_autorizada(usuario, tarea_id, "completar")
    if not servicios.puede_transicionar(tarea["estado"], "completada"):
        raise ErrorApi(400, "La tarea ya está completada")
    db.cambiar_estado(tarea_id, "completada")
    return db.tarea_por_id(tarea_id)


def _publico(usuario):
    return {k: usuario[k] for k in ("id", "email", "nombre", "rol")}


def _json():
    return request.get_json(silent=True) or {}


# ---------- Autenticación ----------

@bp.post("/registro")
def registro():
    datos = _json()
    errores = servicios.validar_registro(datos)
    if errores:
        raise ErrorApi(400, "Datos inválidos", errores)
    try:
        usuario_id = db.crear_usuario(
            servicios.normalizar_email(datos["email"]),
            db.hashear(datos["contrasena"]),
            datos["nombre"].strip(),
        )
    except sqlite3.IntegrityError:
        raise ErrorApi(409, "El email ya está registrado")
    return jsonify(_publico(db.usuario_por_id(usuario_id))), 201


@bp.post("/login")
def login():
    datos = _json()
    usuario = autenticar(datos.get("email"), datos.get("contrasena"))
    if usuario is None:
        raise ErrorApi(401, MENSAJE_LOGIN_FALLIDO)
    session.clear()
    session["usuario_id"] = usuario["id"]
    return jsonify(_publico(usuario))


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(mensaje="Sesión cerrada")


@bp.put("/perfil/contrasena")
def cambiar_contrasena():
    datos = _json()
    if not check_password_hash(g.usuario["password_hash"], datos.get("actual") or ""):
        raise ErrorApi(400, "La contraseña actual no es correcta")
    error = servicios.validar_contrasena(datos.get("nueva"))
    if error:
        raise ErrorApi(400, error)
    db.actualizar_contrasena(g.usuario["id"], db.hashear(datos["nueva"]))
    return jsonify(mensaje="Contraseña actualizada")


# ---------- Tareas ----------

@bp.get("/tareas")
def listar_tareas():
    tareas = servicios.tareas_visibles(g.usuario, db.listar_tareas())
    tareas = servicios.filtrar_tareas(tareas, request.args.get("estado"), request.args.get("q"))
    return jsonify(tareas)


@bp.post("/tareas")
def crear_tarea():
    return jsonify(crear_tarea_para(g.usuario, _json())), 201


@bp.get("/tareas/<int:tarea_id>")
def ver_tarea(tarea_id):
    return jsonify(obtener_tarea_autorizada(g.usuario, tarea_id, "ver"))


@bp.put("/tareas/<int:tarea_id>")
def editar_tarea(tarea_id):
    datos = _json()
    tarea = obtener_tarea_autorizada(g.usuario, tarea_id, "editar")

    version = datos.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ErrorApi(400, "El campo version es obligatorio y debe ser entero")

    cambios, errores = {}, {}
    if "titulo" in datos:
        error = servicios.validar_titulo(datos["titulo"])
        if error:
            errores["titulo"] = error
        else:
            cambios["titulo"] = datos["titulo"].strip()
    if "descripcion" in datos:
        cambios["descripcion"] = (datos["descripcion"] or "").strip() or None
    if "fecha_limite" in datos:
        error = servicios.validar_fecha_limite(datos["fecha_limite"], date.today())
        if error:
            errores["fecha_limite"] = error
        else:
            cambios["fecha_limite"] = servicios.parsear_fecha(datos["fecha_limite"]).isoformat()
    if "estado" in datos and datos["estado"] != tarea["estado"]:
        if servicios.puede_transicionar(tarea["estado"], datos["estado"]):
            cambios["estado"] = datos["estado"]
        else:
            errores["estado"] = f"Transición no permitida: {tarea['estado']} -> {datos['estado']}"
    if "asignado_id" in datos and datos["asignado_id"] != tarea["asignado_id"]:
        if not servicios.puede_reasignar(tarea["estado"]):
            errores["asignado_id"] = "No se puede reasignar una tarea completada; primero reábrala"
        elif db.usuario_por_id(datos["asignado_id"]) is None:
            errores["asignado_id"] = "El usuario asignado no existe"
        else:
            cambios["asignado_id"] = datos["asignado_id"]
    if errores:
        raise ErrorApi(400, "Datos inválidos", errores)

    if not db.actualizar_tarea(tarea_id, version, cambios):
        raise ErrorApi(409, "La tarea fue modificada por otra persona; recargue e intente de nuevo")
    return jsonify(db.tarea_por_id(tarea_id))


@bp.post("/tareas/<int:tarea_id>/completar")
def completar_tarea(tarea_id):
    return jsonify(completar_tarea_para(g.usuario, tarea_id))


@bp.post("/tareas/<int:tarea_id>/reabrir")
def reabrir_tarea(tarea_id):
    tarea = obtener_tarea_autorizada(g.usuario, tarea_id, "ver")
    relacion = servicios.relacion_con(g.usuario["id"], tarea)
    if not servicios.puede_reabrir(g.usuario["rol"], relacion):
        raise ErrorApi(403, "Solo el creador o un admin pueden reabrir la tarea")
    if not servicios.puede_transicionar(tarea["estado"], "pendiente", accion="reabrir"):
        raise ErrorApi(400, "Solo se pueden reabrir tareas completadas")
    db.cambiar_estado(tarea_id, "pendiente")
    return jsonify(db.tarea_por_id(tarea_id))


@bp.delete("/tareas/<int:tarea_id>")
def eliminar_tarea(tarea_id):
    obtener_tarea_autorizada(g.usuario, tarea_id, "eliminar")
    db.eliminar_tarea(tarea_id)
    return "", 204
