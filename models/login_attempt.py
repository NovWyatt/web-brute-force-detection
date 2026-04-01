from datetime import datetime
from extensions import db


class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(45), nullable=False)
    username = db.Column(db.String(80), nullable=True)
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<LoginAttempt {self.ip_address} - {self.username} - {'OK' if self.success else 'FAIL'}>"
