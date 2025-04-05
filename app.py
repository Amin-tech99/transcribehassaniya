# This is the ONLY file Render will look for with its default gunicorn app:app command
# Import standard libraries first
import os
import sys
import logging
import datetime

# Add the current directory to the path so imports work correctly
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

# Now import Flask and extensions
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

# Set up the template and static folders with absolute paths
TEMPLATE_FOLDER = os.path.join(SCRIPT_DIR, 'app', 'templates')
STATIC_FOLDER = os.path.join(SCRIPT_DIR, 'app', 'static')

# Create the Flask application instance
app = Flask(__name__, 
           template_folder=TEMPLATE_FOLDER, 
           static_folder=STATIC_FOLDER)

# Configure the app
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Import models - after db init
try:
    from app.models import User, AudioFile, AudioClip
except ImportError:
    # Logging error but continuing - Render might have a different path structure
    app.logger.error("Failed to import models directly. Trying alternate import path...")
    try:
        # Try with an explicit path-based import
        sys.path.insert(0, os.path.join(SCRIPT_DIR, 'app'))
        from models import User, AudioFile, AudioClip
    except ImportError as e:
        app.logger.error(f"Failed to import models: {e}")
        # We'll continue without models for now to let app at least start

# Template variable injector
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# Import and register blueprints with error handling
try:
    from app.routes import main_bp
    from app.auth import auth_bp
except ImportError:
    app.logger.error("Failed to import blueprints directly. Trying alternate import path...")
    try:
        # Try with explicit imports
        from app.routes import main_bp
    except ImportError as e:
        app.logger.error(f"Failed to import main_bp: {e}")
        # Create an emergency blueprint
        from flask import Blueprint
        main_bp = Blueprint('main', __name__)
        
        @main_bp.route('/')
        def index():
            return render_template('error.html', error="Application is starting up. Try again soon.")
    
    try:
        from app.auth import auth_bp
    except ImportError as e:
        app.logger.error(f"Failed to import auth_bp: {e}")
        # Create an emergency blueprint
        from flask import Blueprint
        auth_bp = Blueprint('auth', __name__)

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

# Create database tables - wrapped in try/except for safety
try:
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")
except Exception as outer_e:
    app.logger.error(f"Failed to enter app context: {outer_e}")

# If running directly, start the app
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
