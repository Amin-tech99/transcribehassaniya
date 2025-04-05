from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hassaniya Transcription App is initializing... Please wait while the application starts."

if __name__ == "__main__":
    app.run()
