"""Vistas HTML mínimas, pensadas para las pruebas E2E con Selenium."""

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from . import db, servicios
from .permisos import puede
from .rutas_api import (
    MENSAJE_LOGIN_FALLIDO,
    ErrorApi,
    autenticar,
    completar_tarea_para,
    crear_tarea_para,
    usuario_actual,
)

bp = Blueprint("web", __name__)


@bp.get("/")
def inicio():
    return redirect(url_for("web.panel"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario = autenticar(request.form.get("email"), request.form.get("contrasena"))
        if usuario:
            session.clear()
            session["usuario_id"] = usuario["id"]
            return redirect(url_for("web.panel"))
        error = MENSAJE_LOGIN_FALLIDO
    return render_template("login.html", error=error)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("web.login"))


@bp.get("/panel")
def panel():
    usuario = usuario_actual()
    if usuario is None:
        return redirect(url_for("web.login"))

    estado = request.args.get("estado", "")
    q = request.args.get("q", "")
    tareas = servicios.tareas_visibles(usuario, db.listar_tareas())
    tareas = servicios.filtrar_tareas(tareas, estado, q)
    for tarea in tareas:
        relacion = servicios.relacion_con(usuario["id"], tarea)
        tarea["puede_completar"] = puede(usuario["rol"], relacion, "completar") and \
            servicios.puede_transicionar(tarea["estado"], "completada")

    usuarios = db.listar_usuarios()
    return render_template(
        "panel.html",
        usuario=usuario,
        tareas=tareas,
        usuarios=usuarios,
        nombres={u["id"]: u["nombre"] for u in usuarios},
        estado=estado,
        q=q,
        hoy=date.today().isoformat(),
    )


@bp.post("/panel/tareas")
def crear_tarea():
    usuario = usuario_actual()
    if usuario is None:
        return redirect(url_for("web.login"))
    try:
        crear_tarea_para(usuario, request.form)
        flash("Tarea creada", "ok")
    except ErrorApi as e:
        flash(" ".join([e.mensaje, *(e.detalles or {}).values()]), "error")
    return redirect(url_for("web.panel"))


@bp.post("/panel/tareas/<int:tarea_id>/completar")
def completar_tarea(tarea_id):
    usuario = usuario_actual()
    if usuario is None:
        return redirect(url_for("web.login"))
    try:
        completar_tarea_para(usuario, tarea_id)
        flash("Tarea completada", "ok")
    except ErrorApi as e:
        flash(e.mensaje, "error")
    return redirect(url_for("web.panel"))
