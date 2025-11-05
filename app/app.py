from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, bcrypt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from app.auth.routes import auth
    from app.core.routes import core
    from app.cars.routes import cars

    app.register_blueprint(core, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(cars, url_prefix="/cars")

    return app
