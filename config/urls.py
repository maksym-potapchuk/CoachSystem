"""Root URL configuration.

API is versioned under /api/v1/. Each domain module exposes its own urls.py
that is included here, keeping module routing self-contained (and easy to
extract into a separate service later).
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

api_v1_patterns = [
    path("", include("apps.users.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1_patterns, "v1"))),
]

# OpenAPI schema + Swagger UI — dev only. Never expose the API surface in prod
if settings.DEBUG:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
    ]
