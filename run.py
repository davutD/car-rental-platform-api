import os
from app.app import create_app

flask_app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", 5005))
    flask_app.run("0.0.0.0", port=port, debug=True)
