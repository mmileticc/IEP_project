"""Wiring every service shares: logging, JWT error handlers, JSON error
responses and an unauthenticated health endpoint."""
import logging
import os

from flask import Blueprint, jsonify

from .errors import register_error_handlers
from .jwt_auth import register_jwt_error_handlers

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


def configure_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def init_common(app, jwt_manager) -> None:
    configure_logging()
    jwt_manager.init_app(app)
    register_jwt_error_handlers(jwt_manager)
    register_error_handlers(app)
    app.register_blueprint(health_bp)
