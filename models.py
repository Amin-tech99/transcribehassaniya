from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    audio_files = db.relationship('AudioFile', backref='uploader', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class AudioFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    processing_error = db.Column(db.Text, nullable=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    clips = db.relationship('AudioClip', backref='audio_file', lazy='dynamic')
    
    def __repr__(self):
        return f'<AudioFile {self.original_filename}>'


class AudioClip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.Float)
    end_time = db.Column(db.Float)
    duration = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transcription = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, assigned, completed, rejected
    audio_file_id = db.Column(db.Integer, db.ForeignKey('audio_file.id'))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    assigned_to = db.relationship('User', backref='assigned_clips', foreign_keys=[assigned_to_id])
    
    def __repr__(self):
        return f'<AudioClip {self.filename} - {self.status}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
