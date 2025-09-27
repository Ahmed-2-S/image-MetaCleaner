import os
import secrets

from flask import Flask
# from flask_login import LoginManager
from auth.routes import auth_bp, login_manager
from main.routes import main_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)  # Prefer managed secret, fallback to random

    # Register filesizeformat filter
    @app.template_filter("filesizeformat")
    def filesizeformat(value):
        """Convert bytes into KB, MB, GB..."""
        try:
            value = int(value)
        except (TypeError, ValueError):
            return "N/A"

        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(value)
        for unit in units:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    # Register Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
