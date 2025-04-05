import os
from flask import Flask

# Create a Flask app for Railway deployment
app = Flask(__name__)

# This allows Railway to set the PORT environment variable
port = int(os.environ.get('PORT', 5000))

# Define your routes
@app.route('/')
def index():
    return "<h1>Hassaniya Transcription App</h1><p>Successfully deployed to Railway!</p>"

# Used by Railway to start the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
