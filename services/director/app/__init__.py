from flask import Flask

from common.app_setup import init_common

from .config import BLOCKCHAIN_ENABLED, Config
from .extensions import jwt
from .routes import bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_common(app, jwt)
    app.register_blueprint(bp)

    if BLOCKCHAIN_ENABLED:
        from .listener import start_listener

        start_listener()

    return app
