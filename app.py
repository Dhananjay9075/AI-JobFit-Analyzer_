import sys
import os

# Add the flask_new directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_new'))

# Import the Flask app from resume_matcher
from resume_matcher import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
