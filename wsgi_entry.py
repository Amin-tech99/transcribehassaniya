# This file is the explicit WSGI entry point for Render
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from config import Config

# Initialize Flask application
app = Flask(__name__, 
           template_folder='app/templates', 
           static_folder='app/static')

# Load configuration
app.config.from_object(Config)

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Import models (after db initialization)
from app.models import User, AudioFile, AudioClip

# Context processor for template variables
@app.context_processor
def inject_now():
    import datetime
    return {'now': datetime.datetime.now()}

# Register blueprints
from app.routes import main_bp
from app.auth import auth_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

# Create database tables if they don't exist
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")

# For local development
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
