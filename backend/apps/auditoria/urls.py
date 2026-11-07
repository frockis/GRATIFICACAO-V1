from rest_framework.routers import SimpleRouter

from .views import RegistroAuditoriaViewSet

router = SimpleRouter()
router.register("auditoria", RegistroAuditoriaViewSet, basename="auditoria")

urlpatterns = router.urls
