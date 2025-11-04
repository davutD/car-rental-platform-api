from app.app import create_app


flask_app = create_app()

if __name__ == "__main__":
    flask_app.run("0.0.0.0", port=5005, debug=True)
