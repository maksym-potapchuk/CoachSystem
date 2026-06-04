# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CoachSystem is the backend for an employee training / learning platform (AI-assisted
features planned later). Django 5 + DRF, built as a **modular monolith**: one project,
strict per-module boundaries, designed so any module can be extracted into its own
service later. Only `apps.common` and `apps.users` exist so far — the learning domain
(courses, lessons, progress, AI tutoring) is yet to be added as new `apps/` modules.

## Commands

Dependency management is **Poetry**; tests use **pytest** via `pytest-django`.

```bash
# Local setup (needs Poetry, Python 3.12+, running Postgres)
poetry install --with dev
poetry run python manage.py migrate
poetry run python manage.py runserver

# Tests — pytest is configured against config.settings.dev (see pyproject.toml)
poetry run pytest                                   # all tests
poetry run pytest apps/users/tests/test_auth_flow.py            # one file
poetry run pytest apps/users/tests/test_auth_flow.py::AuthFlowTests::test_register_login_me  # one test

# Lint / format (line-length 100; ruff selects E,F,I,UP,B)
poetry run ruff check .
poetry run black .

# Migrations after model changes
poetry run python manage.py makemigrations

# Docker (Postgres + web; web auto-runs migrate then runserver)
docker compose up --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
```

When not in Docker, `DJANGO_SETTINGS_MODULE` defaults are split: pytest forces
`config.settings.dev`; `manage.py` / `runserver` rely on the value you set in the
environment (use `config.settings.dev` locally, `config.settings.prod` in production).

## Architecture

**Settings are layered** (`config/settings/`): `base.py` reads all config from the
environment via `django-environ` (`.env` at repo root, see `.env.example`); `dev.py`
and `prod.py` each `from .base import *` and override. `prod.py` calls `env("SECRET_KEY")`
with no default, so production **fails loudly** if the key is unset. Add cross-cutting
config to `base.py`; environment-specific behavior goes in dev/prod.

**Routing is per-module and versioned.** `config/urls.py` mounts everything under
`/api/v1/` by `include()`-ing each module's `urls.py` into the `api_v1_patterns` list,
namespaced as `v1`. Each module's `urls.py` sets `app_name`, so reverse names are
`v1:<module>:<name>` (e.g. `reverse("v1:users:me")` — this is how tests address
endpoints). Swagger UI is at `/api/docs/`, schema at `/api/schema/` (drf-spectacular).

**Auth.** Custom email-login user at `apps.users.models.User` (`AUTH_USER_MODEL =
"users.User"`, `USERNAME_FIELD = "email"`, no username) with a matching `UserManager`.
JWT via `djangorestframework-simplejwt` — login/refresh use SimpleJWT's built-in views;
registration and `/users/me/` are custom DRF generics. DRF defaults to
`IsAuthenticated` globally, so new endpoints are authenticated unless they opt out with
`permission_classes = [AllowAny]` (as `RegisterView` does). Access token 30 min, refresh
7 days, rotating.

**Shared base classes** live in `apps.common` — notably `TimeStampedModel`
(abstract, `created_at`/`updated_at`). Domain models should inherit it rather than
redeclaring timestamp fields.

## Module conventions

Every domain module is a self-contained Django app under `apps/<name>/` with its own
`models.py`, `serializers.py`, `views.py`, `urls.py`, and `tests/`. Modules communicate
through explicit interfaces, **not** by reaching into each other's internals — preserve
this boundary, since it's what keeps a module extractable into a separate service.

To add a module:
1. `poetry run python manage.py startapp <name> apps/<name>`
2. Set `name = "apps.<name>"` in its `AppConfig`.
3. Add `"apps.<name>"` to `LOCAL_APPS` in `config/settings/base.py`.
4. Give it a `urls.py` with `app_name = "<name>"` and include it in `api_v1_patterns`
   in `config/urls.py`.
