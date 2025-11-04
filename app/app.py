from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from app.auth.routes import auth
    from app.core.routes import core

    app.register_blueprint(core, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/auth")

    migrate = Migrate(app, db)

    return app
