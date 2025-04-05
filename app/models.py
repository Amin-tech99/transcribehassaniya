from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    
    clips = db.relationship('AudioClip', backref='transcriber', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AudioFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256))
    original_filename = db.Column(db.String(256))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    progress_percent = db.Column(db.Integer, default=0)  # Track processing progress (0-100)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    clips = db.relationship('AudioClip', backref='source_file', lazy='dynamic')

class AudioClip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256))
    original_file_id = db.Column(db.Integer, db.ForeignKey('audio_file.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    start_time = db.Column(db.Float)
    end_time = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')  # pending, submitted, approved, rejected
    transcription = db.Column(db.Text, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
