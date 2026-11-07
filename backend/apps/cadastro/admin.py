from django.contrib import admin

from .models import Avaliado, Distrito, Unidade
from .services import Autor, salvar


class CadastroAdmin(admin.ModelAdmin):
    """Grava pelo service (valida + audita). Sem exclusão: use status Inativo."""

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        salvar(obj, Autor(nome=request.user.get_username(), perfil=""))


@admin.register(Distrito)
class DistritoAdmin(CadastroAdmin):
    list_display = ["id", "nome"]


@admin.register(Unidade)
class UnidadeAdmin(CadastroAdmin):
    list_display = ["id", "nome", "tipo", "distrito", "cnes", "status"]
    list_filter = ["distrito", "tipo", "status"]
    search_fields = ["nome", "cnes"]


@admin.register(Avaliado)
class AvaliadoAdmin(CadastroAdmin):
    list_display = ["id", "nome", "email", "perfil", "unidade", "distrito", "status"]
    list_filter = ["perfil", "status", "distrito"]
    search_fields = ["nome", "email", "matricula"]
