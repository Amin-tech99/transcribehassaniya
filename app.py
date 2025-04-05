# Direct entry point for Gunicorn
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from config import Config

# Initialize extensions first
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# Create Flask app
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config.from_object(Config)

# Initialize extensions with app
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)

# Context processor for template variables
@app.context_processor
def inject_now():
    import datetime
    return {'now': datetime.datetime.now()}

# Import routes after app is created to avoid circular imports
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

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
