from django.urls import path

from .views import (
    Competencias,
    IndicadorDetalhe,
    Indicadores,
    IndicadoresParaColeta,
    ImportarIndicadores,
    Normativas,
    Regras,
    RegrasParaApuracao,
)

urlpatterns = [
    path("normativas/", Normativas.as_view(), name="normativa-normativas"),
    path("competencias/", Competencias.as_view(), name="normativa-competencias"),
    path("indicadores/importar/", ImportarIndicadores.as_view(), name="normativa-importar"),
    path("indicadores/", Indicadores.as_view(), name="normativa-indicadores"),
    path("indicadores/<int:pk>/", IndicadorDetalhe.as_view(), name="normativa-indicador"),
    path("regras/", Regras.as_view(), name="normativa-regras"),
    path("apuracao/regras/", RegrasParaApuracao.as_view(), name="normativa-regras-apuracao"),
    path("coleta/indicadores/", IndicadoresParaColeta.as_view(), name="normativa-indicadores-coleta"),
]
