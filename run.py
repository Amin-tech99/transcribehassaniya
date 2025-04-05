import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Use environment variables for port if available (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
