import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Brute force detection settings
    MAX_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15
    WINDOW_SECONDS = 300
