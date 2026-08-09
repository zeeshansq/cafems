"""
CafeMS – Development Settings
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# SQLite for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Email to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Media in dev
MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405

# Faster password hashing in development
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
