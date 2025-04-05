from flask import Flask

# Very simple Flask app with no dependencies
app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Hassaniya Transcription App</h1><p>Successfully deployed to Render!</p>"

if __name__ == '__main__':
    app.run()
