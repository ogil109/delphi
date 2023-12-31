import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from flask_session import Session
import logging
from logging.handlers import RotatingFileHandler


# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
scheduler = APScheduler()
migrate = Migrate()
session = Session()


def create_tables(app):
    from .oauth.models import Token, TokenRefreshJob

    with app.app_context():
        db.create_all()


def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    migrate.init_app(app, db)
    session.init_app(app)

    # Create db tables if empty
    create_tables(app)

    # Attach the scheduler to the app
    app.scheduler = scheduler

    # Register the Blueprint
    from .oauth.views import main

    app.register_blueprint(main)

    # Logging setup
    if not app.debug:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.DEBUG)
        app.logger.info("Your app logger is ready")

    @login_manager.user_loader
    def load_user(request_id):
        from .oauth.models import Token

        return Token.get_by_request(request_id)

    app.logger.info("App created successfully.")
    return app
