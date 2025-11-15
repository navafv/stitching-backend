from .base import *

# --- Development-specific settings ---

DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# --- Database ---
# Use local sqlite3 for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Email ---
# Use console backend for local development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# --- Logging ---
# Show all DEBUG messages in development
LOGGING["root"]["level"] = "DEBUG"

# --- Django Debug Toolbar ---
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1"]