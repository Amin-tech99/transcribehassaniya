import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    try:
        from flaskapp.routes import main_bp
        app.register_blueprint(main_bp)
    except ImportError:
        # Create a simple route if the main blueprint is not available
        @app.route('/')
        def index():
            return 'Hassaniya Transcription App'
            
    try:
        from flaskapp.auth import auth_bp
        app.register_blueprint(auth_bp)
    except ImportError:
        pass
    
    # Context processor for template variables
    @app.context_processor
    def inject_now():
        import datetime
        return {'now': datetime.datetime.now()}
    
    # Create database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Error creating database tables: {e}")
    
    return app

# Create the Flask app
app = create_app()

if __name__ == '__main__':
    # Use environment variables for port if available (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
