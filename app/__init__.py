from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# Create a reference to the app instance for Gunicorn
app = None

def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    
    # Initialize app with config specific settings
    if hasattr(config_class, 'init_app'):
        config_class.init_app(flask_app)
    
    # Register blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    
    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(auth_bp)
    
    # Context processor for template variables
    @flask_app.context_processor
    def inject_now():
        import datetime
        return {'now': datetime.datetime.now()}
    
    # Create database tables if they don't exist
    with flask_app.app_context():
        try:
            db.create_all()
        except Exception as e:
            flask_app.logger.error(f"Database initialization error: {e}")
    
    # Set the global app variable for Gunicorn to use directly
    global app
    app = flask_app
    
    return flask_app
