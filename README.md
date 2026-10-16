# Web Brute Force Detection

> **Repo này không còn phát triển.** Ý tưởng đã được viết lại thành package Laravel
> **[novwyatt/laravel-login-guard](https://github.com/NovWyatt/laravel-login-guard)**
> ([Packagist](https://packagist.org/packages/novwyatt/laravel-login-guard)), có test tự động và CI.
> Bản Flask bên dưới giữ lại để tham khảo.

| | Bản Flask này | laravel-login-guard |
|---|---|---|
| Đếm lần sai | Theo IP và username: 5 lần trong 5 phút | Theo username (5 lần) và IP (20 lần) trong 15 phút, chỉnh được |
| Khóa | Cố định 15 phút | Tăng dần 1, 2, 4… phút, tối đa 1 ngày |
| Lưu bộ đếm | `dict` trong RAM, mất khi khởi động lại | Cache của Laravel (database, Redis…); trạng thái khóa ở database |
| Danh sách IP | Không có | Cho phép / chặn, dải CIDR, IPv6 |
| Cảnh báo | Email SMTP | Mail, Slack, Telegram; tối đa 1 lần mỗi giờ cho mỗi đối tượng |
| Quản trị | Dashboard web | Lệnh `login-guard:list`, `login-guard:unlock`; sự kiện `LoginLocked`, `SuspiciousActivity` |
| Gắn vào ứng dụng | Code đăng nhập riêng của app | Nghe sự kiện đăng nhập của Laravel: mọi `Auth::attempt()` (Fortify, Breeze…) được bảo vệ |
| Kiểm thử | Không có | 51 test Pest, Larastan mức max, CI PHP 8.3 / 8.4 × Laravel 12 / 13 |

Flask web app phát hiện và chặn tấn công brute force login. Tự động khóa IP và username sau nhiều lần đăng nhập thất bại, ghi log chi tiết, và cung cấp admin dashboard để giám sát hệ thống.

## Tính năng

- 🔐 Form login với **CSRF protection** (Flask-WTF)
- 🚫 Tự động **khóa IP** sau 5 lần đăng nhập sai trong 5 phút
- 👤 Tự động **khóa username** sau 5 lần sai (chống tấn công nhắm vào 1 tài khoản)
- 📋 Ghi log toàn bộ lần thử (IP, username, timestamp, user-agent, kết quả)
- 📊 **Admin dashboard** xem thống kê, danh sách IP/username bị khóa, mở khóa thủ công
- 🔍 **Filter log** theo IP / trạng thái (thành công/thất bại) / ngày
- 📧 **Email cảnh báo** khi phát hiện tấn công brute force (tùy chọn, gửi async)
- ⏱️ **Countdown timer** hiển thị thời gian còn bị khóa cho người dùng
- 🔒 Mã hóa password bằng **bcrypt**

## Tech Stack

| Thành phần       | Development              | Production (khuyến nghị) |
|------------------|--------------------------|--------------------------|
| Language         | Python 3.11              | Python 3.11              |
| Framework        | Flask 3.0                | Flask 3.0                |
| Database         | SQLite (file-based)      | PostgreSQL               |
| Rate Limit Store | In-memory dict           | Redis                    |
| CSRF             | Flask-WTF                | Flask-WTF                |
| Password Hash    | bcrypt                   | bcrypt                   |
| WSGI Server      | Flask dev server         | Gunicorn                 |
| Reverse Proxy    | —                        | Nginx                    |

## Cấu trúc thư mục

```
web-brute-force-detection/
├── app.py                          # Flask app factory, khởi tạo DB + CSRF + blueprints
├── config.py                       # Cấu hình (MAX_ATTEMPTS, LOCKOUT_MINUTES, ...)
├── extensions.py                   # SQLAlchemy instance dùng chung
├── requirements.txt                # Dependencies
├── .env                            # Biến môi trường (SECRET_KEY, SMTP, ...)
│
├── models/
│   ├── __init__.py                 # Export User, LoginAttempt
│   ├── user.py                     # Model User (id, username, password_hash, created_at)
│   └── login_attempt.py            # Model LoginAttempt (id, ip, username, success, timestamp, ua)
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py             # Xác thực: verify_password, authenticate
│   ├── brute_force.py              # Rate limit: IP + username tracking, lock/unlock
│   └── alert_service.py            # Gửi email cảnh báo async khi phát hiện tấn công
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                     # Blueprint "auth": /login, /dashboard, /logout
│   └── admin.py                    # Blueprint "admin": /admin/dashboard, /admin/logs, unlock
│
├── templates/
│   ├── login.html                  # Form đăng nhập + locked screen + countdown
│   └── admin/
│       ├── dashboard.html          # Admin dashboard: stats, locked IPs/usernames, recent logs
│       └── logs.html               # Admin logs: filter + bảng kết quả
│
├── static/
│   └── style.css                   # Toàn bộ CSS (login card + admin sidebar/tables/badges)
│
└── instance/
    └── app.db                      # SQLite database (tự tạo khi chạy app)
```

## Chạy local

### 1. Clone repository

```bash
git clone https://github.com/NovWyatt/web-brute-force-detection.git
cd web-brute-force-detection
```

### 2. Tạo virtual environment (khuyến nghị)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Cài dependencies

```bash
pip install -r requirements.txt
```

### 4. Tạo file .env

```bash
# Copy từ mẫu hoặc tạo mới
cp .env.example .env
```

Hoặc tạo file `.env` với nội dung tối thiểu:

```
SECRET_KEY=your-secret-key-here
ALERT_ENABLED=false
```

### 5. Chạy app

```bash
python app.py
```

App sẽ chạy tại: **http://127.0.0.1:5000**

> Lần đầu chạy, app tự tạo database `instance/app.db` và seed tài khoản test.

## Tài khoản test mặc định

| Username | Password   |
|----------|------------|
| `admin`  | `admin123` |

> ⚠️ **Lưu ý**: Đổi password ngay khi deploy lên production.

## Biến môi trường (.env)

| Biến               | Mô tả                                          | Giá trị mặc định          |
|--------------------|-------------------------------------------------|----------------------------|
| `SECRET_KEY`       | Khóa bí mật cho session và CSRF                | `your-secret-key-here`     |
| `ALERT_ENABLED`    | Bật/tắt gửi email cảnh báo (`true` / `false`)  | `false`                    |
| `ALERT_EMAIL_TO`   | Email nhận cảnh báo                             | `your@email.com`           |
| `ALERT_EMAIL_FROM` | Email gửi cảnh báo (hiển thị trong From)        | `alert@yourapp.com`        |
| `SMTP_HOST`        | SMTP server                                     | `smtp.gmail.com`           |
| `SMTP_PORT`        | SMTP port (TLS)                                 | `587`                      |
| `SMTP_USER`        | SMTP username (thường là email)                 | `your@gmail.com`           |
| `SMTP_PASSWORD`    | SMTP password hoặc App Password                 | `your-app-password`        |

## Cấu hình brute force

Các hằng số trong `config.py`:

| Hằng số            | Giá trị | Mô tả                                                    |
|--------------------|---------|-----------------------------------------------------------|
| `MAX_ATTEMPTS`     | `5`     | Số lần đăng nhập sai tối đa trước khi bị khóa            |
| `LOCKOUT_MINUTES`  | `15`    | Thời gian khóa (phút) sau khi vượt ngưỡng                |
| `WINDOW_SECONDS`   | `300`   | Cửa sổ thời gian (giây) để đếm số lần sai (5 phút)      |

**Cách hoạt động**: Nếu một IP hoặc username đăng nhập sai **5 lần trong vòng 5 phút**, IP/username đó sẽ bị khóa **15 phút**. Sau 15 phút tự động mở khóa, hoặc admin có thể mở khóa thủ công qua dashboard.

## Các trang chính

| URL                | Mô tả                                  |
|--------------------|-----------------------------------------|
| `/login`           | Trang đăng nhập                         |
| `/dashboard`       | Trang chính sau đăng nhập               |
| `/logout`          | Đăng xuất                               |
| `/admin/dashboard` | Admin dashboard: thống kê + quản lý     |
| `/admin/logs`      | Admin logs: xem & filter lịch sử login  |

## License

MIT
