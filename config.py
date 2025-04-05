import os
import re

# Try to import dotenv, but continue if not available
try:
    from dotenv import load_dotenv
    basedir = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(basedir, '.env'))
except ImportError:
    print("Warning: python-dotenv not installed, using default environment variables")
    basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hassaniya-transcription-secret-key'
    
    # Handle PostgreSQL URLs from Render (convert postgres:// to postgresql://)
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    
    # These settings help with database connection persistence
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Check connection before use
        'pool_recycle': 280,   # Recycle connections before Render's 30min timeout
        'pool_timeout': 20,    # Timeout for getting connection from pool
        'pool_size': 10        # Maximum number of connections to keep in pool
    }
    
    # File storage paths
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    RAW_AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, 'raw')
    CLIPS_FOLDER = os.path.join(UPLOAD_FOLDER, 'clips')
    EXPORT_FOLDER = os.path.join(UPLOAD_FOLDER, 'exports')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max upload size
    
    # Ensure uploads directories exist
    @staticmethod
    def init_app(app):
        # Create upload directories if they don't exist
        for folder in [app.config['UPLOAD_FOLDER'], app.config['RAW_AUDIO_FOLDER'], 
                       app.config['CLIPS_FOLDER'], app.config['EXPORT_FOLDER']]:
            os.makedirs(folder, exist_ok=True)
