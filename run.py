import os
from dotenv import load_dotenv
from app import create_app

# Load local environment variables from .env file if available
load_dotenv()

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    app.run(host=host, port=port, debug=debug)
