"""Development settings."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

# Browsable API is handy in dev.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Permissive CORS for local frontend development.
CORS_ALLOW_ALL_ORIGINS = env("CORS_ALLOW_ALL_ORIGINS", default=True)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
