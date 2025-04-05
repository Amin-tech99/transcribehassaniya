import os
import sys
import logging
from flask import Flask, render_template_string

# Set up logging to help debug crashes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Flask app for Railway deployment
app = Flask(__name__)

# Configure the app with essential settings
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# This allows Railway to set the PORT environment variable
port = int(os.environ.get('PORT', 5000))

# Simple landing page template
LANDING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Hassaniya Transcription App</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #2c3e50; }
        .info { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Hassaniya Transcription App</h1>
    <div class="info">
        <p><strong>Status:</strong> The application is running on Railway!</p>
        <p>This is a simplified version of the application for deployment testing.</p>
        <p>Server information: Python {{ python_version }}</p>
    </div>
</body>
</html>
"""

# Error handler for 500 errors
@app.errorhandler(500)
def server_error(e):
    logger.exception('An error occurred during a request.')
    return "<h1>Internal Server Error</h1><p>The application encountered an error. Administrators have been notified.</p>", 500

# Define your routes
@app.route('/')
def index():
    try:
        return render_template_string(LANDING_PAGE, python_version=sys.version)
    except Exception as e:
        logger.exception("Error rendering index page")
        return f"<h1>Hassaniya Transcription App</h1><p>App is running, but encountered a minor error: {str(e)}</p>"

# Used by Railway to start the application
if __name__ == '__main__':
    try:
        logger.info(f"Starting application on port {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        sys.exit(1)
