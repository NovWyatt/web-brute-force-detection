from datetime import datetime, timedelta

from config import Config

# In-memory stores — reset when the process restarts
failed_attempts: dict = {}
# format: { "192.168.1.1": {"count": 3, "first_attempt": datetime} }

locked_ips: dict = {}
# format: { "192.168.1.1": datetime_khi_unlock }


def is_ip_locked(ip: str) -> bool:
    """Check whether *ip* is currently locked out.

    If the lock has expired, the entry is removed and False is returned.
    """
    if ip not in locked_ips:
        return False

    if datetime.utcnow() >= locked_ips[ip]:
        locked_ips.pop(ip)
        return False

    return True


def record_failed_attempt(ip: str) -> None:
    """Record a failed login attempt from *ip*.

    Resets the window if WINDOW_SECONDS has elapsed since the first
    attempt.  Locks the IP when the count reaches MAX_ATTEMPTS.
    """
    now = datetime.utcnow()

    if ip not in failed_attempts:
        failed_attempts[ip] = {"count": 1, "first_attempt": now}
    else:
        entry = failed_attempts[ip]
        elapsed = (now - entry["first_attempt"]).total_seconds()

        if elapsed > Config.WINDOW_SECONDS:
            # Window expired — start a fresh window
            failed_attempts[ip] = {"count": 1, "first_attempt": now}
        else:
            entry["count"] += 1

    # Lock the IP if threshold reached
    if failed_attempts[ip]["count"] >= Config.MAX_ATTEMPTS:
        unlock_time = now + timedelta(minutes=Config.LOCKOUT_MINUTES)
        locked_ips[ip] = unlock_time
        failed_attempts.pop(ip)


def reset_attempts(ip: str) -> None:
    """Clear all tracking data for *ip* (failed attempts and lock)."""
    failed_attempts.pop(ip, None)
    locked_ips.pop(ip, None)


def get_remaining_lockout(ip: str) -> int:
    """Return the number of seconds *ip* remains locked, or 0 if unlocked."""
    if ip not in locked_ips:
        return 0

    remaining = (locked_ips[ip] - datetime.utcnow()).total_seconds()
    return max(int(remaining), 0)
