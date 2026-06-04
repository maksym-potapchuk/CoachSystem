"""
Base settings shared across all environments.

Environment-specific settings live in dev.py / prod.py and import from here.
Secrets and environment-dependent values are read from the environment via
django-environ. See .env.example for the full list.
"""
from datetime import timedelta
from pathlib import Path

import environ
import structlog

# config/settings/base.py -> BASE_DIR is the repo root (three parents up).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOW_ALL_ORIGINS=(bool, False),
)

# Read .env from repo root if present (no-op in containers using real env vars).
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    # Stores blacklisted/outstanding refresh tokens (enables logout + rotation
    # invalidation). Needs its migrations applied: manage.py migrate.
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    # Structured logging: binds a request_id (and user_id) to every log line
    # emitted during a request — the cheap precursor to distributed tracing.
    "django_structlog",
]

# Domain modules live under apps/. Add new modules here.
LOCAL_APPS = [
    "apps.common",
    "apps.users",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Last, and after AuthenticationMiddleware, so it can bind the resolved
    # user_id. Emits request_started / request_finished / request_failed and
    # makes request_id available to every logger downstream.
    "django_structlog.middlewares.RequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database (PostgreSQL via DATABASE_URL)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://coach:coach@localhost:5432/coach",
    ),
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Cookies
# ---------------------------------------------------------------------------
# The API authenticates via the Authorization header (bearer JWT), so these
# only govern Django's own session/CSRF cookies (admin, browsable API). Lax
# lets top-level navigations send them while blocking cross-site POSTs.
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# ---------------------------------------------------------------------------
# DRF + JWT
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Throttling. Global defaults cover every endpoint; the "auth" scope is
    # applied explicitly to login/register (see views.py) to blunt brute-force.
    # NOTE: throttle counters live in Django's cache. The default LocMemCache is
    # per-process and correct for a single worker. Only when prod runs multiple
    # workers do counts stop being shared — at that point switch CACHES to a
    # shared backend (DatabaseCache on the existing Postgres is enough; Redis
    # only if something else needs it). Serious brute-force defense belongs at
    # the edge (nginx/WAF) + account lockout, not this layer.
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", default="30/min"),
        "user": env("THROTTLE_USER", default="120/min"),
        "auth": env("THROTTLE_AUTH", default="10/min"),
    },
}

SIMPLE_JWT = {
    # Token lifetimes.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Rotation: every refresh issues a new refresh token and blacklists the old
    # one, so a leaked refresh token is single-use. Requires the
    # token_blacklist app (see INSTALLED_APPS) and its migrations.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    # Touch User.last_login on login/refresh.
    "UPDATE_LAST_LOGIN": True,
    # Signing — defaults to SECRET_KEY; pinned explicitly for clarity.
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUDIENCE": None,
    "ISSUER": None,
    # Header format: "Authorization: Bearer <token>".
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    # Claims mapping.
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "CoachSystem API",
    "DESCRIPTION": "Employee training / learning platform — backend API.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Split request/response schemas so read-only fields (id, date_joined, ...)
    # don't show up as writable inputs in the docs.
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    # Strip the version prefix so endpoints are auto-grouped by their first path
    # segment — "auth/..." and "users/..." become tags on their own, no
    # per-view decorators needed. The names below just add the descriptions.
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "TAGS": [
        {"name": "auth", "description": "Registration and JWT token lifecycle."},
        {"name": "users", "description": "The authenticated user's own account."},
    ],
    "SWAGGER_UI_SETTINGS": {
        # Keep the bearer token in the browser across page reloads, so you
        # don't re-Authorize after every refresh (token still expires per
        # SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]).
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "docExpansion": "list",
    },
}

# ---------------------------------------------------------------------------
# Logging (structlog)
# ---------------------------------------------------------------------------
# Pattern: one shared processing pipeline (structlog.configure) feeds stdlib
# logging; the final *render* is a swappable strategy chosen per environment.
# dev keeps the colourful console renderer; prod flips the handler to JSON
# (see dev.py / prod.py). Everything goes to stdout — collection is the
# runtime's job (12-factor), not the app's.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
    },
    "handlers": {
        # Default formatter is console; prod.py swaps it for "json".
        "console": {"class": "logging.StreamHandler", "formatter": "console"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django_structlog": {"level": "INFO"},
        "apps": {"level": "INFO"},  # our domain modules
        # SQL is noisy; raise to DEBUG only when chasing a query.
        "django.db.backends": {"level": "WARNING"},
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,  # pulls in request_id / user_id
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        # Hand off to the stdlib ProcessorFormatter, which renders per handler.
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# 
# Static files---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
