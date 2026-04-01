from datetime import datetime

from flask import Blueprint, render_template, request, redirect, session, flash

from extensions import db
from models.user import User
from models.login_attempt import LoginAttempt
from services.brute_force import (
    locked_ips,
    reset_attempts,
    get_remaining_lockout,
    locked_usernames,
    reset_username_attempts,
    get_username_remaining_lockout,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_login():
    """Return the logged-in User or None (caller should redirect)."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return User.query.get(user_id)


@admin_bp.route("/dashboard", methods=["GET"])
def dashboard():
    user = _require_login()
    if user is None:
        return redirect("/login")

    # --- Stats ---
    total_attempts = LoginAttempt.query.count()
    total_failed = LoginAttempt.query.filter_by(success=False).count()
    total_success = LoginAttempt.query.filter_by(success=True).count()
    unique_ips = db.session.query(
        db.func.count(db.func.distinct(LoginAttempt.ip_address))
    ).scalar()

    # --- Locked IPs (from in-memory dict) ---
    now = datetime.utcnow()
    locked_list = []
    for ip, unlock_time in list(locked_ips.items()):
        remaining = max(int((unlock_time - now).total_seconds()), 0)
        if remaining > 0:
            locked_list.append({
                "ip": ip,
                "unlock_time": unlock_time.strftime("%Y-%m-%d %H:%M:%S"),
                "remaining": remaining,
            })

    # --- Locked usernames (from in-memory dict) ---
    locked_user_list = []
    for uname, unlock_time in list(locked_usernames.items()):
        remaining = max(int((unlock_time - now).total_seconds()), 0)
        if remaining > 0:
            locked_user_list.append({
                "username": uname,
                "unlock_time": unlock_time.strftime("%Y-%m-%d %H:%M:%S"),
                "remaining": remaining,
            })

    # --- Recent logs (20 newest) ---
    recent_logs = (
        LoginAttempt.query
        .order_by(LoginAttempt.timestamp.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        user=user,
        total_attempts=total_attempts,
        total_failed=total_failed,
        total_success=total_success,
        unique_ips=unique_ips,
        locked_list=locked_list,
        locked_user_list=locked_user_list,
        recent_logs=recent_logs,
    )


@admin_bp.route("/unlock/<ip>", methods=["POST"])
def unlock_ip(ip):
    user = _require_login()
    if user is None:
        return redirect("/login")

    reset_attempts(ip)
    flash(f"Đã mở khóa IP: {ip}", "success")
    return redirect("/admin/dashboard")


@admin_bp.route("/unlock-username/<username>", methods=["POST"])
def unlock_username(username):
    user = _require_login()
    if user is None:
        return redirect("/login")

    reset_username_attempts(username)
    flash(f"Đã mở khóa username: {username}", "success")
    return redirect("/admin/dashboard")


@admin_bp.route("/logs", methods=["GET"])
def logs():
    user = _require_login()
    if user is None:
        return redirect("/login")

    # --- Filters ---
    filter_ip = request.args.get("ip", "").strip()
    filter_status = request.args.get("status", "").strip()
    filter_from = request.args.get("from", "").strip()

    query = LoginAttempt.query

    if filter_ip:
        query = query.filter(LoginAttempt.ip_address == filter_ip)

    if filter_status == "success":
        query = query.filter(LoginAttempt.success == True)  # noqa: E712
    elif filter_status == "failed":
        query = query.filter(LoginAttempt.success == False)  # noqa: E712

    if filter_from:
        try:
            from_date = datetime.strptime(filter_from, "%Y-%m-%d")
            query = query.filter(LoginAttempt.timestamp >= from_date)
        except ValueError:
            pass  # ignore bad date format

    results = query.order_by(LoginAttempt.timestamp.desc()).limit(100).all()
    total_results = query.count()

    return render_template(
        "admin/logs.html",
        user=user,
        results=results,
        total_results=total_results,
        filter_ip=filter_ip,
        filter_status=filter_status,
        filter_from=filter_from,
    )
