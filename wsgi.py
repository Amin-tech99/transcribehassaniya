import os
import sys
from flask import Flask, redirect, url_for

# Create a simple application first to ensure Render can start the server
app = Flask(__name__)

@app.route('/')
def home():
    try:
        # Try to import the actual application
        from flaskapp import create_app
        # If successful, replace our simple app with the real one
        global app
        app = create_app()
        return redirect(url_for('main.index'))
    except Exception as e:
        # If there's an error, show a message with the error
        return f"<h1>Hassaniya Transcription App is initializing...</h1><p>Error: {str(e)}</p>"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
