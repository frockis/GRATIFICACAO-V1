from django.contrib import admin

from .models import Competencia, Indicador, Normativa, RegraCalculo


@admin.register(Normativa)
class NormativaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "vigencia_inicio", "vigencia_fim", "situacao")
    search_fields = ("codigo", "nome", "referencia_portaria")


@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ("ano", "mes", "normativa")
    list_filter = ("ano", "normativa")


@admin.register(Indicador)
class IndicadorAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "nivel", "normativa", "ativo")
    list_filter = ("nivel", "ativo", "normativa")
    search_fields = ("codigo", "nome")


@admin.register(RegraCalculo)
class RegraCalculoAdmin(admin.ModelAdmin):
    list_display = (
        "indicador",
        "cargo",
        "tipo_unidade",
        "peso_portaria",
        "peso_excepcional",
        "meta",
    )
    list_filter = ("cargo", "tipo_unidade")
    search_fields = ("indicador__codigo", "indicador__nome", "abrangencia")
