import os
import torch
import torchaudio
import json
import zipfile
from datetime import datetime
from app import db
from app.models import AudioFile, AudioClip
from flask import current_app
import uuid

def process_audio_file(audio_file_path, original_filename, audio_file_id):
    """Process the uploaded audio file using Silero VAD to split it into clips"""
    
    # Get the audio file from the database for progress updates
    audio_file = AudioFile.query.get(audio_file_id)
    
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
    
    # Initialize progress
    update_progress('initializing', 5)
    
    # Load the Silero VAD model
    try:
        update_progress('loading_model', 10)
        model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                    model='silero_vad',
                                    force_reload=False)  # Set to False to use cached model when available
        
        (get_speech_timestamps, save_audio, read_audio, _, _) = utils
        update_progress('model_loaded', 20)
    except Exception as e:
        print(f"Error loading model: {e}")
        update_progress('error', 0)
        return 0
    
    # Read audio file
    sampling_rate = 16000
    try:
        update_progress('reading_audio', 30)
        # Handle different audio formats by converting to wav with required sample rate
        if not audio_file_path.lower().endswith('.wav'):
            temp_path = os.path.join(current_app.config['RAW_AUDIO_FOLDER'], f"temp_{uuid.uuid4().hex}.wav")
            waveform, orig_sr = torchaudio.load(audio_file_path)
            if orig_sr != sampling_rate:
                resampler = torchaudio.transforms.Resample(orig_freq=orig_sr, new_freq=sampling_rate)
                waveform = resampler(waveform)
            torchaudio.save(temp_path, waveform, sampling_rate)
            audio_file_path = temp_path
            
        audio = read_audio(audio_file_path, sampling_rate=sampling_rate)
        update_progress('audio_read', 40)
    except Exception as e:
        print(f"Error processing audio file: {e}")
        update_progress('error', 0)
        return 0
    
    # Get speech timestamps
    try:
        update_progress('detecting_speech', 50)
        timestamps = get_speech_timestamps(audio, model, sampling_rate=sampling_rate, 
                                        min_speech_duration_ms=1000,  # Minimum 1 second
                                        max_speech_duration_s=15,     # Maximum 15 seconds
                                        min_silence_duration_ms=500)  # 500ms silence denotes a break
        update_progress('speech_detected', 70)
    except Exception as e:
        print(f"Error detecting speech: {e}")
        update_progress('error', 0)
        return 0
    
    # Process and save clips
    clips_folder = current_app.config['CLIPS_FOLDER']
    timestamp_now = datetime.now().strftime("%Y%m%d%H%M%S")
    base_filename = os.path.splitext(os.path.basename(original_filename))[0]
    
    if len(timestamps) == 0:
        update_progress('no_speech_found', 90)
        # Mark the original file as processed even if no clips were found
        audio_file.processed = True
        db.session.commit()
        # Clean up progress file
        if os.path.exists(progress_file):
            os.remove(progress_file)
        return 0
    
    update_progress('creating_clips', 80)
    
    # Calculate progress step for each clip
    progress_per_clip = 15 / len(timestamps)
    
    for i, ts in enumerate(timestamps):
        # Create clip filename
        clip_filename = f"{base_filename}_{timestamp_now}_clip_{i+1}.wav"
        clip_path = os.path.join(clips_folder, clip_filename)
        
        # Save audio clip
        save_audio(clip_path, audio[ts['start']:ts['end']], sampling_rate=sampling_rate)
        
        # Create database entry for the clip
        clip = AudioClip(
            filename=clip_filename,
            original_file_id=audio_file_id,
            start_time=ts['start'] / sampling_rate,
            end_time=ts['end'] / sampling_rate
        )
        db.session.add(clip)
        
        # Update progress for each clip
        current_progress = 80 + (i + 1) * progress_per_clip
        update_progress('processing_clips', min(95, int(current_progress)))
    
    db.session.commit()
    
    # Mark the original file as processed
    audio_file.processed = True
    db.session.commit()
    
    # Final progress update
    update_progress('completed', 100)
    
    # Clean up progress file after a brief delay to allow final update to be read
    # In a production app, you might want to keep these for a longer period or use a database
    try:
        import time
        time.sleep(1)  # Wait for 1 second to ensure clients can see 100%
        if os.path.exists(progress_file):
            os.remove(progress_file)
    except:
        pass
    
    return len(timestamps)

def export_dataset(export_path=None):
    """Export approved clips as a JSONL dataset for Whisper fine-tuning"""
    
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

def auto_assign_clips(transcribers):
    """Automatically assign unassigned clips to transcribers in a balanced way"""
    if not transcribers:
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
