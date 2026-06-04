# CoachSystem

Backend for an **employee training / learning platform** (AI-assisted features
planned for later). Built with Django 5 + Django REST Framework as a **modular
monolith** — one project, clean module boundaries, ready to be split into
microservices when a module needs to scale independently.

## Architecture

```
config/                 # project package (settings, urls, wsgi/asgi)
  settings/
    base.py             # shared settings, reads .env via django-environ
    dev.py              # DEBUG, browsable API, permissive CORS
    prod.py             # hardened, fails if SECRET_KEY missing
apps/                   # domain modules — each is a self-contained Django app
  common/               # shared base classes (TimeStampedModel, ...)
  users/                # auth + accounts (JWT, custom email-based User)
pyproject.toml          # Poetry — deps (main / dev group / prod extra)
poetry.lock
manage.py
docker-compose.yml      # db (Postgres 16) + web (Django)
Dockerfile
```

**Modular-monolith intent:** every domain lives under `apps/<module>/` with its
own `models`, `serializers`, `views`, `urls`, and `tests`. Modules talk through
explicit interfaces, not by reaching into each other's internals. The learning
domain (courses, lessons, progress, and later AI tutoring) will be added as new
modules under `apps/` — and any module can be extracted into its own service
later with minimal churn.

## Tech

- Django 5, Django REST Framework
- JWT auth (`djangorestframework-simplejwt`) — custom **email-login** User
- PostgreSQL 16
- `drf-spectacular` for OpenAPI + Swagger
- `django-environ` for config, `django-cors-headers` for CORS
- **Poetry** for dependency management

## Quickstart (Docker)

```bash
cp .env.example .env          # then set a real SECRET_KEY
docker compose up --build     # starts Postgres + Django, runs migrations
```

API is then at http://localhost:8000/

- Swagger UI:    http://localhost:8000/api/docs/
- OpenAPI schema: http://localhost:8000/api/schema/
- Django admin:  http://localhost:8000/admin/

Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

## Local (no Docker)

Requires [Poetry](https://python-poetry.org/docs/#installation), a running
PostgreSQL, and Python 3.12+.

```bash
poetry install --with dev       # creates a virtualenv and installs everything
cp .env.example .env            # point DATABASE_URL at your local Postgres

poetry run python manage.py migrate
poetry run python manage.py runserver
```

Run commands inside the env with `poetry run <cmd>`, or open a subshell with
`poetry shell` (plugin) and drop the prefix. Production-only deps:
`poetry install --extras prod`.

## Tests

```bash
poetry run pytest
# or
poetry run python manage.py test
```

## API (v1)

All endpoints are versioned under `/api/v1/`.

| Method     | Path                  | Auth   | Description                          |
|------------|-----------------------|--------|--------------------------------------|
| POST       | `/auth/register/`     | public | Register (email, password, names)    |
| POST       | `/auth/login/`        | public | Obtain JWT access + refresh          |
| POST       | `/auth/refresh/`      | public | Refresh access token                 |
| GET/PATCH  | `/users/me/`          | JWT    | Get / update the current user        |

Authenticate by sending `Authorization: Bearer <access_token>`.

### Example

```bash
# register
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"emp@example.com","password":"Str0ng-Passw0rd!","first_name":"Test","last_name":"Employee"}'

# login -> { "access": "...", "refresh": "..." }
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"emp@example.com","password":"Str0ng-Passw0rd!"}'

# me
curl http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer <access>"
```

## Adding a new module

```bash
mkdir apps/<name>
python manage.py startapp <name> apps/<name>
```

