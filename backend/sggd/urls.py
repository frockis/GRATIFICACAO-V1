"""Rotas do SGGD. Cada componente (apps/<componente>) publica as suas rotas em /api/."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.cadastro.urls")),
    path("api/", include("apps.auditoria.urls")),
    path("api/normativa/", include("apps.normativa.urls")),
]
