from flask import Blueprint, render_template, request, redirect, session, url_for

from config import Config
from extensions import db
from models.user import User
from models.login_attempt import LoginAttempt
from services.auth_service import authenticate
from services.brute_force import (
    is_ip_locked,
    record_failed_attempt,
    reset_attempts,
    get_remaining_lockout,
    failed_attempts,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    ip = request.remote_addr
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    user_agent = request.headers.get("User-Agent", "")

    # --- 1. Check if IP is locked ---
    if is_ip_locked(ip):
        attempt = LoginAttempt(
            ip_address=ip,
            username=username,
            success=False,
            user_agent=user_agent,
        )
        db.session.add(attempt)
        db.session.commit()

        return render_template(
            "login.html",
            error="Quá nhiều lần thử. Vui lòng thử lại sau.",
            locked=True,
            retry_after=get_remaining_lockout(ip),
        )

    # --- 2. Authenticate ---
    user = authenticate(username, password)

    if user is None:
        # Wrong credentials
        record_failed_attempt(ip)

        attempt = LoginAttempt(
            ip_address=ip,
            username=username,
            success=False,
            user_agent=user_agent,
        )
        db.session.add(attempt)
        db.session.commit()

        # Calculate remaining attempts
        entry = failed_attempts.get(ip)
        current_count = entry["count"] if entry else 0
        attempts_left = Config.MAX_ATTEMPTS - current_count

        return render_template(
            "login.html",
            error="Sai tên đăng nhập hoặc mật khẩu.",
            attempts_left=attempts_left,
        )

    # --- 3. Login successful ---
    reset_attempts(ip)

    attempt = LoginAttempt(
        ip_address=ip,
        username=username,
        success=True,
        user_agent=user_agent,
    )
    db.session.add(attempt)
    db.session.commit()

    session["user_id"] = user.id
    return redirect("/dashboard")


@auth_bp.route("/dashboard", methods=["GET"])
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])
    if user is None:
        session.clear()
        return redirect("/login")

    return f"Xin chào {user.username}! <a href='/logout'>Đăng xuất</a>"


@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/login")
