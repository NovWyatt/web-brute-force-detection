import os
import smtplib
import threading
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_alert_email(ip: str, username: str, attempt_count: int) -> None:
    """Send an alert email about a brute force attack.

    Runs in a background thread so it never blocks the request.
    If ALERT_ENABLED is not "true", or any error occurs, the function
    silently returns without raising.
    """
    if os.environ.get("ALERT_ENABLED", "false").lower() != "true":
        return

    def _send():
        try:
            to_addr = os.environ.get("ALERT_EMAIL_TO", "")
            from_addr = os.environ.get("ALERT_EMAIL_FROM", "")
            smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            smtp_user = os.environ.get("SMTP_USER", "")
            smtp_pass = os.environ.get("SMTP_PASSWORD", "")

            if not to_addr or not from_addr:
                print("[ALERT] Thiếu ALERT_EMAIL_TO hoặc ALERT_EMAIL_FROM, bỏ qua.")
                return

            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

            subject = "[CẢNH BÁO] Phát hiện tấn công brute force"

            body = (
                f"⚠️ CẢNH BÁO BẢO MẬT\n"
                f"{'=' * 40}\n\n"
                f"Phát hiện tấn công brute force trên hệ thống.\n\n"
                f"📋 Chi tiết:\n"
                f"  • IP tấn công:      {ip}\n"
                f"  • Username mục tiêu: {username}\n"
                f"  • Số lần thử:       {attempt_count}\n"
                f"  • Thời gian:        {now}\n\n"
                f"🔒 IP đã bị khóa tự động.\n\n"
                f"👉 Kiểm tra chi tiết tại: /admin/dashboard\n\n"
                f"---\n"
                f"Web Brute Force Detection System\n"
            )

            msg = MIMEMultipart()
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_addr, to_addr, msg.as_string())

            print(f"[ALERT] Email cảnh báo đã gửi đến {to_addr}")

        except Exception as e:
            print(f"[ALERT WARNING] Không thể gửi email cảnh báo: {e}")

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
