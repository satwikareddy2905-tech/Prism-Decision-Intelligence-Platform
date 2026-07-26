import os
from flask import Flask
from app.config import config
from app.extensions import db, login_manager, bcrypt, csrf, migrate


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Import models to register them with SQLAlchemy
    with app.app_context():
        from app.models import (  # noqa: F401
            User, Decision, Criterion, Option, CustomAttribute,
            Score, JournalEntry, ActivityLog, Notification
        )
        db.create_all()

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.decisions import decisions_bp
    from app.blueprints.api import api_bp
    from app.blueprints.comparison import comparison_bp
    from app.blueprints.journal import journal_bp
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.search import search_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.profile import profile_bp

    app.url_map.strict_slashes = False

    app.register_blueprint(auth_bp)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(decisions_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(comparison_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(profile_bp)

    # Register error handlers
    from app.blueprints.errors import register_error_handlers
    register_error_handlers(app)

    # Register template filters
    from app.utils.helpers import register_template_filters
    register_template_filters(app)

    return app
