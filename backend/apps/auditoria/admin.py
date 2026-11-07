from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ["data_hora", "componente", "usuario", "perfil", "operacao", "registro_afetado"]
    list_filter = ["componente", "operacao"]
    search_fields = ["usuario", "registro_afetado"]

    # Log não se edita nem se apaga (requisitos de segurança).
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
