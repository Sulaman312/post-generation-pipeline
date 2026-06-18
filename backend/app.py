"""Flask application factory."""

import logging

from flask import Flask
from flask_cors import CORS

from backend.api.routes import api_bp
from backend.logging_config import configure_logging, register_request_logging

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    configure_logging(level=logging.INFO)
    logger.info("ContentFlow backend starting")

    app = Flask(__name__)
    # Match prior FastAPI behavior: allow browser dev servers on any port (:3000, :3001, …).
    CORS(
        app,
        resources={
            r"/*": {
                "origins": "*",
                "methods": ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": "*",
            }
        },
    )
    register_request_logging(app)
    app.register_blueprint(api_bp)
    return app
