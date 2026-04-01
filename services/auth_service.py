from typing import Optional

import bcrypt

from models.user import User


def verify_password(plain_text: str, hashed: str) -> bool:
    """Compare a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_text.encode("utf-8"),
        hashed.encode("utf-8"),
    )


def get_user_by_username(username: str) -> Optional[User]:
    """Return the User with the given username, or None if not found."""
    return User.query.filter_by(username=username).first()


def authenticate(username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password.

    Returns the User object on success, or None if the user does not
    exist or the password is incorrect.
    """
    user = get_user_by_username(username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
