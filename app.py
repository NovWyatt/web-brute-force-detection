from flask import Flask
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from config import Config
from extensions import db
import bcrypt

load_dotenv()

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    app.register_blueprint(auth_bp, url_prefix="")
    app.register_blueprint(admin_bp)

    with app.app_context():
        # Import models so SQLAlchemy knows about them before create_all()
        from models import User, LoginAttempt

        db.create_all()

        # Seed test user if not exists
        if not User.query.filter_by(username="admin").first():
            hashed = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt())
            admin = User(
                username="admin",
                password_hash=hashed.decode("utf-8"),
            )
            db.session.add(admin)
            db.session.commit()
            print("[SEED] Created test user: admin / admin123")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
