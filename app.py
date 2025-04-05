# This is the ONLY file Render will look for with its default gunicorn app:app command
# Import Flask and extensions
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from config import Config

# Create app
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Import models - after db init
from app.models import User, AudioFile, AudioClip

# Template variable injector
@app.context_processor
def inject_now():
    import datetime
    return {'now': datetime.datetime.now()}

# Import and register blueprints
from app.routes import main_bp
from app.auth import auth_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

# Create database tables
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")

# If running directly, start the app
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
