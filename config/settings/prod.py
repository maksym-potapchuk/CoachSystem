"""Production settings."""
from .base import *  # noqa: F401,F403
from .base import LOGGING, env

DEBUG = False

# Render logs as one JSON object per line for the log aggregator.
LOGGING["handlers"]["console"]["formatter"] = "json"

# Fail loudly if SECRET_KEY is left at the insecure default.
SECRET_KEY = env("SECRET_KEY")

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# Security hardening.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
