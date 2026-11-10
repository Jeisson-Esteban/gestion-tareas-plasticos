import os

from flask import Flask

from . import db


def create_app(config=None):
    """Fábrica de la app. En pruebas se pasa {'DATABASE': ruta_temporal}."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-solo-local"),
        DATABASE=os.path.join(app.instance_path, "tareas.sqlite"),
        HASH_METODO="scrypt",
    )
    if config:
        app.config.update(config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from . import rutas_api, rutas_web
    app.register_blueprint(rutas_api.bp)
    app.register_blueprint(rutas_web.bp)
    return app
