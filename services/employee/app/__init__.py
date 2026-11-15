from flask import Flask

from common.app_setup import init_common

from .config import Config
from .extensions import jwt
from .routes import bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_common(app, jwt)
    app.register_blueprint(bp)

    return app
