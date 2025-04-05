from flask import Flask, render_template_string, request, redirect, url_for
import os

# Create the basic Flask app that Render can find
app = Flask(__name__)

# Set a secret key for session security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# Define a simple HTML template for the landing page
LANDING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Hassaniya Transcription App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        .button {
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
        .message {
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }
    </style>
</head>
<body>
    <h1>Hassaniya Transcription App</h1>
    <div class="message">
        <p>The application is now running on Render!</p>
        <p>This is a simple landing page created for deployment testing.</p>
        <p>You are seeing this page because the app is successfully running but may need further configuration.</p>
    </div>
    <p>The full application features include:</p>
    <ul>
        <li>User authentication for admins and transcribers</li>
        <li>Audio clip uploading and transcription</li>
        <li>Admin dashboard for managing clips and users</li>
        <li>Transcriber interface for working on assigned clips</li>
        <li>Batch upload of pre-processed audio clips via ZIP files</li>
    </ul>
    <p>
        <a href="https://github.com/Amin-tech99/transcribehassaniya" class="button">View on GitHub</a>
    </p>
</body>
</html>
"""

# Define the main route
@app.route('/')
def index():
    return render_template_string(LANDING_PAGE)

# Run the app
if __name__ == '__main__':
    # Use environment variables for port if available (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
