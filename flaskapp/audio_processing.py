import os
import json
import zipfile
from datetime import datetime
from flaskapp import db
from flaskapp.models import AudioFile, AudioClip
from flask import current_app
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_audio_file(audio_file_path, original_filename, audio_file_id):
    """Process the uploaded audio file using pydub to split it into clips.
    This is a simple version that divides the audio into equal parts."""
    try:
        # Import audio processing library
        from pydub import AudioSegment
        import math
        
        # Get the audio file from the database
        audio_file = AudioFile.query.get(audio_file_id)
        if not audio_file:
            logger.error(f"Audio file with ID {audio_file_id} not found")
            return 0
        
        # Create temp progress file for tracking
        progress_folder = os.path.join(current_app.config['EXPORT_FOLDER'], 'progress')
        os.makedirs(progress_folder, exist_ok=True)
        progress_file = os.path.join(progress_folder, f"progress_{audio_file_id}.json")
        
        def update_progress(stage, percent):
            # Write progress to a JSON file that can be read by the web app
            progress_data = {
                'file_id': audio_file_id,
                'stage': stage,
                'percent': percent,
                'timestamp': datetime.now().isoformat()
            }
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f)
            # Also update the database
            if audio_file:
                audio_file.progress_percent = percent
                db.session.commit()
        
        # Initialize progress
        update_progress('initializing', 5)
        update_progress('loading_audio', 20)
        
        # Load the audio file with pydub
        try:
            audio = AudioSegment.from_file(audio_file_path)
            duration_ms = len(audio)
            update_progress('audio_loaded', 30)
        except Exception as e:
            logger.error(f"Error loading audio file: {e}")
            update_progress('error', 0)
            return 0
        
        # Create a fixed number of clips (10 clips or less for shorter files)
        total_clips = min(10, math.ceil(duration_ms / 30000))  # Max 10 clips, minimum 30 seconds each
        clip_duration = duration_ms / total_clips
        
        update_progress('creating_clips', 40)
        
        clips_folder = current_app.config['CLIPS_FOLDER']
        os.makedirs(clips_folder, exist_ok=True)
        
        # Create the clips
        clip_count = 0
        for i in range(total_clips):
            start_time = i * clip_duration
            end_time = (i + 1) * clip_duration
            
            clip = audio[start_time:end_time]
            clip_filename = f"clip_{audio_file_id}_{i+1}.wav"
            clip_path = os.path.join(clips_folder, clip_filename)
            
            # Export the clip
            clip.export(clip_path, format="wav")
            
            # Create record in database
            audioclip = AudioClip(
                filename=clip_filename,
                start_time=start_time / 1000,  # Convert to seconds
                end_time=end_time / 1000,      # Convert to seconds
                duration=(end_time - start_time) / 1000,  # Convert to seconds
                audio_file_id=audio_file_id,
                status='pending'
            )
            db.session.add(audioclip)
            clip_count += 1
            
            # Update progress
            progress = 40 + (i + 1) * (50 / total_clips)
            update_progress('processing_clips', int(progress))
        
        # Commit all clips to database
        db.session.commit()
        
        # Update the audio file record
        audio_file.processed = True
        audio_file.progress_percent = 100
        db.session.commit()
        
        update_progress('completed', 100)
        return clip_count
        
    except Exception as e:
        logger.error(f"Error in audio processing: {e}")
        if 'update_progress' in locals():
            update_progress('error', 0)
        return 0

def export_dataset(export_path=None):
    """Export approved clips as a JSONL dataset for model fine-tuning"""
    
    approved_clips = AudioClip.query.filter_by(status='approved').all()
    
    if not approved_clips:
        return None
        
    clips_folder = current_app.config['CLIPS_FOLDER']
    export_folder = current_app.config['EXPORT_FOLDER']
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create export folder if it doesn't exist
    os.makedirs(export_folder, exist_ok=True)
    
    # Create zip file path if not provided
    if export_path is None:
        export_path = os.path.join(export_folder, f"transcription_dataset_{timestamp}.zip")
    
    # Create zip file
    with zipfile.ZipFile(export_path, 'w') as zip_file:
        # Create a JSONL file for the dataset
        jsonl_content = ""
        
        for clip in approved_clips:
            clip_path = os.path.join(clips_folder, clip.filename)
            
            # Skip if the clip file doesn't exist
            if not os.path.exists(clip_path):
                continue
            
            # Add clip to zip file
            zip_file.write(clip_path, arcname=clip.filename)
            
            # Add entry to JSONL content
            entry = {
                "audio_filepath": clip.filename,
                "text": clip.transcription
            }
            jsonl_content += json.dumps(entry) + "\n"
        
        # Write JSONL file to the zip
        jsonl_filename = "transcription_dataset.jsonl"
        zip_file.writestr(jsonl_filename, jsonl_content)
    
    return export_path

def auto_assign_clips(transcribers=None):
    """Automatically assign unassigned clips to transcribers"""
    if not transcribers or len(transcribers) == 0:
        # Get all non-admin users
        from app.models import User
        transcribers = User.query.filter_by(is_admin=False).all()
    
    if not transcribers or len(transcribers) == 0:
        return 0
        
    # Get unassigned clips
    unassigned_clips = AudioClip.query.filter_by(assigned_to=None).all()
    
    if not unassigned_clips:
        return 0
        
    # Create a round-robin assignment
    count = 0
    for i, clip in enumerate(unassigned_clips):
        transcriber = transcribers[i % len(transcribers)]
        clip.assigned_to = transcriber.id
        count += 1
    
    db.session.commit()
    return count
