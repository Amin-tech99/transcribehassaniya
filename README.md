# Hassaniya Arabic Transcription Application

A collaborative web application for transcribing Hassaniya Arabic audio and preparing datasets for Whisper fine-tuning.

## Features

- **Audio Processing Pipeline**: Upload long-form audio, remove silence, and split into manageable segments
- **Collaboration**: Assign transcription tasks to team members
- **Quality Control**: Admin review and approval process for transcriptions
- **Export**: Generate Whisper-compatible JSONL dataset for fine-tuning
- **Mobile Responsive**: Optimized interface for both desktop and mobile devices

## Technology Stack

- **Backend**: Python/Flask
- **Database**: SQLite (local), PostgreSQL (production)
- **Audio Processing**: Silero-VAD, PyTorch
- **Frontend**: Bootstrap 5, JavaScript
- **Deployment**: Render (web service with persistent disk)

## Local Setup Instructions

### Prerequisites

- Python 3.8+ installed
- Git (for cloning the repository)

### Installation

1. Clone the repository:
   ```
   git clone [your-repository-url]
   cd [repository-directory]
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

### Running the Application Locally

1. Start the Flask development server:
   ```
   python run.py
   ```

2. Access the application at http://localhost:5000

## Deployment on Render

This application is configured for easy deployment on Render with data persistence.

### Prerequisites for Deployment

- A Render account
- Git repository with your code

### Deployment Steps

1. **Create a new Web Service on Render**:
   - Connect your GitHub/GitLab repository
   - Select the branch to deploy

2. **Configuration**:
   - **Name**: Choose a name for your service
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`

3. **Environment Variables**:
   Add the following environment variables:
   - `FLASK_APP=run.py`
   - `FLASK_ENV=production`
   - `SECRET_KEY=[Generate a secure random string]`
   - `DATABASE_URL=[Your PostgreSQL URL]` (Render will provide this if you add a PostgreSQL database)

4. **Set Up Persistent Disk**:
   - In your service settings, navigate to the "Disks" tab
   - Create a new disk with at least 1GB storage
   - Mount path: `/opt/render/project/src/app/static/uploads`

5. **Deploy**:
   - Click "Create Web Service"
   - Render will automatically build and deploy your application
   - The first deployment might take a few minutes

6. **Database Migration**:
   - After deployment, run database migrations using Render's shell access:
     ```
     flask db upgrade
     python update_db.py
     ```

7. **First-Time Setup**:
   - Register the first user who will automatically become an admin
   - Continue setup as described in the Usage Guide

## User Roles

### Admin

- Upload and process audio files
- Assign clips to transcribers
- Review transcriptions
- Export the final dataset

### Transcriber

- View assigned clips
- Submit transcriptions
- Check feedback from admin

## Usage Guide

### First-Time Setup

1. Register the first user who will automatically become an admin
2. Login with the admin account
3. Register additional users for transcribers
4. Upload audio files for transcription

### Workflow

1. **Admin**: Upload audio through the upload page
2. **Admin**: Assign clips to transcribers (manually or auto-assign)
3. **Transcribers**: Transcribe assigned clips
4. **Admin**: Review and approve/reject transcriptions
5. **Admin**: Export the final dataset for Whisper fine-tuning

## Whisper Fine-Tuning

The exported dataset will be in JSONL format, compatible with OpenAI's Whisper fine-tuning:

```json
{"audio_filepath": "clip_1.wav", "text": "Transcription text in Hassaniya Arabic"}
{"audio_filepath": "clip_2.wav", "text": "Another transcription example"}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
