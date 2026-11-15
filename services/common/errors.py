"""JSON error responses shared by all three services."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from .validation import ValidationError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def _handle_validation_error(error: ValidationError):
        return jsonify({"message": error.message}), 400

    @app.errorhandler(404)
    def _handle_not_found(_error):
        return jsonify({"message": "Not found."}), 404

    @app.errorhandler(405)
    def _handle_method_not_allowed(_error):
        return jsonify({"message": "Method not allowed."}), 405

    @app.errorhandler(Exception)
    def _handle_unexpected_error(error: Exception):
        # Flask routes every HTTPException without a more specific handler
        # here too; keep its status code instead of turning it into a 500.
        if isinstance(error, HTTPException):
            return jsonify({"message": error.description}), error.code
        logger.exception("Unhandled error while processing request")
        return jsonify({"message": "Internal server error."}), 500
