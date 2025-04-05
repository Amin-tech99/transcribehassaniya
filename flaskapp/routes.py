from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, AudioFile, AudioClip
from app.audio_processing import process_audio_file, export_dataset, auto_assign_clips
import os
from datetime import datetime
import uuid

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    elif current_user.is_admin:
        return redirect(url_for('main.admin_dashboard'))
    else:
        return redirect(url_for('main.transcriber_dashboard'))

@main_bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin dashboard')
        return redirect(url_for('main.transcriber_dashboard'))
    
    # Get statistics for the dashboard
    total_audio_files = AudioFile.query.count()
    total_clips = AudioClip.query.count()
    pending_clips = AudioClip.query.filter_by(status='pending').count()
    submitted_clips = AudioClip.query.filter_by(status='submitted').count()
    approved_clips = AudioClip.query.filter_by(status='approved').count()
    rejected_clips = AudioClip.query.filter_by(status='rejected').count()
    
    # Get recent uploads
    recent_uploads = AudioFile.query.order_by(AudioFile.upload_date.desc()).limit(5).all()
    
    # Get unprocessed audio file IDs for JavaScript
    unprocessed_ids = [audio.id for audio in recent_uploads if not audio.processed]
    
    # Get transcribers
    transcribers = User.query.filter_by(is_admin=False).all()
    
    # Get clips that need review (submitted but not approved/rejected)
    clips_for_review = AudioClip.query.filter_by(status='submitted').order_by(AudioClip.updated_at.desc()).all()
    
    # Get unassigned clips
    unassigned_clips = AudioClip.query.filter_by(assigned_to=None).all()
    
    return render_template('admin/dashboard.html', 
                          total_audio_files=total_audio_files,
                          total_clips=total_clips,
                          pending_clips=pending_clips,
                          submitted_clips=submitted_clips,
                          approved_clips=approved_clips,
                          rejected_clips=rejected_clips,
                          recent_uploads=recent_uploads,
                          transcribers=transcribers,
                          clips_for_review=clips_for_review,
                          unassigned_clips=unassigned_clips,
                          unprocessed_ids=unprocessed_ids)

@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_audio():
    if not current_user.is_admin:
        flash('You do not have permission to upload audio files')
        return redirect(url_for('main.transcriber_dashboard'))
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file:
            # Secure the filename and generate a unique name to store it
            original_filename = secure_filename(file.filename)
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            
            # Create the file paths
            file_path = os.path.join(current_app.config['RAW_AUDIO_FOLDER'], unique_filename)
            
            # Save the file
            file.save(file_path)
            
            # Create database entry for the file
            audio_file = AudioFile(
                filename=unique_filename,
                original_filename=original_filename,
                uploaded_by=current_user.id
            )
            db.session.add(audio_file)
            db.session.commit()
            
            # Process the audio file
            try:
                num_clips = process_audio_file(file_path, original_filename, audio_file.id)
                flash(f'Successfully processed audio file and created {num_clips} clips')
            except Exception as e:
                flash(f'Error processing audio file: {str(e)}')
                
            return redirect(url_for('main.admin_dashboard'))
    
    return render_template('admin/upload.html')

@main_bp.route('/upload_clips_zip', methods=['GET', 'POST'])
@login_required
def upload_clips_zip():
    """Upload a zip file containing pre-processed audio clips"""
    if not current_user.is_admin:
        flash('You do not have permission to upload clips')
        return redirect(url_for('main.transcriber_dashboard'))
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and file.filename.lower().endswith('.zip'):
            # Process the zip file
            try:
                # Create a temporary file to extract the zip
                import tempfile
                import zipfile
                
                # Save the zip file temporarily
                zip_path = os.path.join(tempfile.gettempdir(), f"clips_{uuid.uuid4().hex}.zip")
                file.save(zip_path)
                
                # Create database entry for the source upload
                source_name = os.path.splitext(secure_filename(file.filename))[0]
                audio_file = AudioFile(
                    filename=f"{source_name}_zip.mp3",  # Placeholder filename
                    original_filename=file.filename,
                    uploaded_by=current_user.id,
                    processed=True  # Mark as processed since clips are pre-processed
                )
                db.session.add(audio_file)
                db.session.commit()
                
                # Extract and process the clips
                clips_folder = current_app.config['CLIPS_FOLDER']
                os.makedirs(clips_folder, exist_ok=True)
                
                clip_count = 0
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Get list of audio files in the zip
                    audio_files = [f for f in zip_ref.namelist() 
                                 if f.lower().endswith(('.wav', '.mp3', '.ogg', '.flac'))]
                    
                    for i, clip_path in enumerate(audio_files):
                        # Extract clip to clips folder
                        filename = os.path.basename(clip_path)
                        safe_filename = f"clip_{audio_file.id}_{i+1}_{secure_filename(filename)}"
                        
                        # Extract the file
                        zip_ref.extract(clip_path, clips_folder)
                        extracted_path = os.path.join(clips_folder, clip_path)
                        
                        # If file is in a subfolder, move it to clips folder with safe name
                        if os.path.dirname(clip_path):
                            os.rename(extracted_path, os.path.join(clips_folder, safe_filename))
                        else:
                            # If already in root of zip, just rename it
                            os.rename(os.path.join(clips_folder, filename), 
                                    os.path.join(clips_folder, safe_filename))
                        
                        # Create clip entry in database
                        clip = AudioClip(
                            filename=safe_filename,
                            start_time=0,  # We don't know the real times
                            end_time=30,   # Placeholder duration
                            duration=30,    # Placeholder duration
                            audio_file_id=audio_file.id,
                            status='pending'
                        )
                        db.session.add(clip)
                        clip_count += 1
                
                # Commit all clips to database
                db.session.commit()
                
                # Clean up
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                
                flash(f'Successfully extracted {clip_count} clips from the zip file')
                return redirect(url_for('main.admin_dashboard'))
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                flash(f'Error processing zip file: {str(e)}')
                return redirect(request.url)
        else:
            flash('Please upload a ZIP file containing audio clips')
            return redirect(request.url)
    
    return render_template('admin/upload_clips_zip.html')

@main_bp.route('/transcriber')
@login_required
def transcriber_dashboard():
    # Get assigned clips for the current transcriber
    assigned_clips = AudioClip.query.filter_by(assigned_to=current_user.id).all()
    
    # Count clips by status
    pending_count = sum(1 for clip in assigned_clips if clip.status == 'pending')
    submitted_count = sum(1 for clip in assigned_clips if clip.status == 'submitted')
    approved_count = sum(1 for clip in assigned_clips if clip.status == 'approved')
    rejected_count = sum(1 for clip in assigned_clips if clip.status == 'rejected')
    
    return render_template('transcriber/dashboard.html',
                          assigned_clips=assigned_clips,
                          pending_count=pending_count,
                          submitted_count=submitted_count,
                          approved_count=approved_count,
                          rejected_count=rejected_count)

@main_bp.route('/transcribe/<int:clip_id>', methods=['GET', 'POST'])
@login_required
def transcribe_clip(clip_id):
    clip = AudioClip.query.get_or_404(clip_id)
    
    # Check if the clip is assigned to the current user
    if clip.assigned_to != current_user.id and not current_user.is_admin:
        flash('You do not have permission to transcribe this clip')
        return redirect(url_for('main.transcriber_dashboard'))
    
    if request.method == 'POST':
        transcription = request.form.get('transcription')
        
        if transcription:
            clip.transcription = transcription
            clip.status = 'submitted'
            clip.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Transcription submitted successfully')
            return redirect(url_for('main.transcriber_dashboard'))
        else:
            flash('Transcription cannot be empty')
    
    # Get the clip's audio URL
    clip_url = url_for('static', filename=f'uploads/clips/{clip.filename}')
    
    return render_template('transcriber/transcribe.html', clip=clip, clip_url=clip_url)

@main_bp.route('/review/<int:clip_id>', methods=['GET', 'POST'])
@login_required
def review_clip(clip_id):
    if not current_user.is_admin:
        flash('You do not have permission to review transcriptions')
        return redirect(url_for('main.transcriber_dashboard'))
    
    clip = AudioClip.query.get_or_404(clip_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        edited_transcription = request.form.get('transcription')
        feedback = request.form.get('feedback', '')
        
        if action == 'approve':
            clip.status = 'approved'
            if edited_transcription:
                clip.transcription = edited_transcription
            clip.feedback = feedback
        elif action == 'reject':
            clip.status = 'rejected'
            if edited_transcription:
                clip.transcription = edited_transcription
            clip.feedback = feedback
        
        clip.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Transcription {action}d successfully')
        return redirect(url_for('main.admin_dashboard'))
    
    # Get the clip's audio URL
    clip_url = url_for('static', filename=f'uploads/clips/{clip.filename}')
    
    return render_template('admin/review.html', clip=clip, clip_url=clip_url)

@main_bp.route('/assign', methods=['POST'])
@login_required
def assign_clips():
    if not current_user.is_admin:
        flash('You do not have permission to assign clips')
        return redirect(url_for('main.transcriber_dashboard'))
    
    clip_ids = request.form.getlist('clip_ids[]')
    transcriber_id = request.form.get('transcriber_id')
    
    if not clip_ids or not transcriber_id:
        flash('Please select clips and a transcriber')
        return redirect(url_for('main.admin_dashboard'))
    
    transcriber = User.query.get(transcriber_id)
    if not transcriber or transcriber.is_admin:
        flash('Invalid transcriber selected')
        return redirect(url_for('main.admin_dashboard'))
    
    for clip_id in clip_ids:
        clip = AudioClip.query.get(clip_id)
        if clip:
            clip.assigned_to = transcriber.id
    
    db.session.commit()
    flash(f'{len(clip_ids)} clips assigned to {transcriber.username}')
    return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/auto-assign', methods=['POST'])
@login_required
def auto_assign():
    if not current_user.is_admin:
        flash('You do not have permission to auto-assign clips')
        return redirect(url_for('main.transcriber_dashboard'))
    
    transcribers = User.query.filter_by(is_admin=False).all()
    
    if not transcribers:
        flash('No transcribers available for assignment')
        return redirect(url_for('main.admin_dashboard'))
    
    num_assigned = auto_assign_clips(transcribers)
    
    flash(f'Automatically assigned {num_assigned} clips to transcribers')
    return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/export')
@login_required
def export():
    if not current_user.is_admin:
        flash('You do not have permission to export data')
        return redirect(url_for('main.transcriber_dashboard'))
    
    export_path = export_dataset()
    
    if export_path:
        return send_file(export_path, as_attachment=True)
    else:
        flash('No approved transcriptions available for export')
        return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/manage-users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('You do not have permission to manage users')
        return redirect(url_for('main.transcriber_dashboard'))
    
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@main_bp.route('/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to change user roles')
        return redirect(url_for('main.transcriber_dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin role from oneself
    if user.id == current_user.id:
        flash('You cannot change your own role')
        return redirect(url_for('main.manage_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f'Updated role for {user.username}')
    return redirect(url_for('main.manage_users'))


@main_bp.route('/quick-approve/<int:clip_id>', methods=['POST'])
@login_required
def quick_approve(clip_id):
    if not current_user.is_admin:
        flash('You do not have permission to approve transcriptions')
        return redirect(url_for('main.transcriber_dashboard'))
    
    clip = AudioClip.query.get_or_404(clip_id)
    
    # Update clip status to approved
    clip.status = 'approved'
    clip.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Transcription for clip {clip.filename} has been approved')
    return redirect(url_for('main.admin_dashboard'))


@main_bp.route('/quick-reject/<int:clip_id>', methods=['POST'])
@login_required
def quick_reject(clip_id):
    if not current_user.is_admin:
        flash('You do not have permission to reject transcriptions')
        return redirect(url_for('main.transcriber_dashboard'))
    
    clip = AudioClip.query.get_or_404(clip_id)
    
    # Update clip status to rejected
    clip.status = 'rejected'
    clip.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Transcription for clip {clip.filename} has been rejected')
    return redirect(url_for('main.admin_dashboard'))


@main_bp.route('/delete-clip/<int:clip_id>', methods=['POST'])
@login_required
def delete_clip(clip_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete clips')
        return redirect(url_for('main.transcriber_dashboard'))
    
    clip = AudioClip.query.get_or_404(clip_id)
    
    # Get the clip's file path to delete the file
    clip_path = os.path.join(current_app.config['CLIPS_FOLDER'], clip.filename)
    
    # Delete the file if it exists
    if os.path.exists(clip_path):
        try:
            os.remove(clip_path)
        except OSError as e:
            flash(f'Error deleting file: {e}')
    
    # Store filename for flash message
    filename = clip.filename
    
    # Delete the database record
    db.session.delete(clip)
    db.session.commit()
    
    flash(f'Clip {filename} has been deleted')
    return redirect(url_for('main.admin_dashboard'))


@main_bp.route('/delete-audio/<int:audio_id>', methods=['POST'])
@login_required
def delete_audio(audio_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete audio files')
        return redirect(url_for('main.transcriber_dashboard'))
    
    audio_file = AudioFile.query.get_or_404(audio_id)
    
    # Get the audio file path to delete the file
    file_path = os.path.join(current_app.config['RAW_AUDIO_FOLDER'], audio_file.filename)
    
    # Delete the file if it exists
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            flash(f'Error deleting file: {e}')
    
    # Get all associated clips
    clips = AudioClip.query.filter_by(original_file_id=audio_id).all()
    
    # Delete all associated clip files
    for clip in clips:
        clip_path = os.path.join(current_app.config['CLIPS_FOLDER'], clip.filename)
        if os.path.exists(clip_path):
            try:
                os.remove(clip_path)
            except OSError:
                pass
    
    # Store filename for flash message
    filename = audio_file.original_filename
    
    # Delete the audio file record (will cascade delete clips)
    db.session.delete(audio_file)
    db.session.commit()
    
    flash(f'Audio file {filename} and all associated clips have been deleted')
    return redirect(url_for('main.admin_dashboard'))


@main_bp.route('/audio-progress/<int:audio_id>', methods=['GET'])
@login_required
def get_audio_progress(audio_id):
    if not current_user.is_admin:
        return {"error": "Unauthorized"}, 403
    
    # Get the audio file
    audio_file = AudioFile.query.get_or_404(audio_id)
    
    # If already processed, return 100%
    if audio_file.processed:
        return {
            "file_id": audio_id,
            "stage": "completed",
            "percent": 100
        }
    
    # Check for progress file
    progress_folder = os.path.join(current_app.config['EXPORT_FOLDER'], 'progress')
    progress_file = os.path.join(progress_folder, f"progress_{audio_id}.json")
    
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
                return progress_data
        except:
            pass
    
    # Default if no progress file exists but file is not marked as processed
    return {
        "file_id": audio_id,
        "stage": "processing",
        "percent": 0
    }
