import os

from dotenv import load_dotenv
from flask import Flask


env = os.getenv("NODE_ENV", "development")
load_dotenv(f".env.{env}")

from routes.devices import devices_bp
from routes.events import events_bp
from routes.frames import frames_bp


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    app.register_blueprint(devices_bp, url_prefix="/api/v1/devices")
    app.register_blueprint(events_bp, url_prefix="/api/v1/events")
    app.register_blueprint(frames_bp, url_prefix="/api/v1/frames")

    @app.get("/")
    def index():
        return "Hello World!"

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    app.run(host="0.0.0.0", port=port)
