from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("distritos", views.DistritoViewSet, basename="distrito")
router.register("unidades", views.UnidadeViewSet, basename="unidade")
router.register("usuarios", views.UsuarioViewSet, basename="usuario")

urlpatterns = [
    path("vinculos/", views.vinculos, name="vinculos"),
    path("cadastro/importar/", views.importar, name="cadastro-importar"),
    *router.urls,
]
