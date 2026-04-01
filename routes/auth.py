from flask import Blueprint, render_template, request, redirect, session, url_for

from config import Config
from extensions import db
from models.user import User
from models.login_attempt import LoginAttempt
from services.auth_service import authenticate
from services.alert_service import send_alert_email
from services.brute_force import (
    is_ip_locked,
    record_failed_attempt,
    reset_attempts,
    get_remaining_lockout,
    failed_attempts,
    is_username_locked,
    record_failed_username,
    reset_username_attempts,
    get_username_remaining_lockout,
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

    # --- 2. Check if username is locked ---
    if username and is_username_locked(username):
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
            error="Tài khoản này tạm thời bị khóa do quá nhiều lần thử sai.",
            locked=True,
            retry_after=get_username_remaining_lockout(username),
        )

    # --- 3. Authenticate ---
    user = authenticate(username, password)

    if user is None:
        # Wrong credentials — track both IP and username
        ip_just_locked = record_failed_attempt(ip)
        username_just_locked = record_failed_username(username) if username else False

        attempt = LoginAttempt(
            ip_address=ip,
            username=username,
            success=False,
            user_agent=user_agent,
        )
        db.session.add(attempt)
        db.session.commit()

        # Send alert email if IP was just locked
        if ip_just_locked:
            send_alert_email(ip, username, Config.MAX_ATTEMPTS)

        # Calculate remaining attempts (use IP counter)
        entry = failed_attempts.get(ip)
        current_count = entry["count"] if entry else 0
        attempts_left = Config.MAX_ATTEMPTS - current_count

        return render_template(
            "login.html",
            error="Sai tên đăng nhập hoặc mật khẩu.",
            attempts_left=attempts_left,
        )

    # --- 4. Login successful ---
    reset_attempts(ip)
    reset_username_attempts(username)

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

    return (
        f"<div style='padding:24px;font-family:Segoe UI,sans-serif'>"
        f"<h2>Xin chào {user.username}!</h2>"
        f"<p style='margin:16px 0'>"
        f"<a href='/admin/dashboard' style='color:#2563eb;margin-right:16px'>📊 Admin Dashboard</a>"
        f"<a href='/logout' style='color:#dc2626'>🚪 Đăng xuất</a>"
        f"</p></div>"
    )


@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/login")
