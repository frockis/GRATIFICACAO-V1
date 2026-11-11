from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Consulta técnica. O rastro não se edita pelo admin."""

    list_display = (
        "ocorrido_em",
        "usuario_identificacao",
        "operacao",
        "entidade",
        "identificador",
    )
    list_filter = ("entidade", "operacao")
    search_fields = ("identificador", "usuario_identificacao", "valor_novo")
    readonly_fields = (
        "ocorrido_em",
        "usuario",
        "usuario_identificacao",
        "operacao",
        "entidade",
        "identificador",
        "valor_anterior",
        "valor_novo",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
