from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.secret_key = "login123"

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main
    app.register_blueprint(main)

    from app import models 

    return app