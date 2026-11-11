from rest_framework import serializers

from .models import Competencia, Indicador, Normativa, RegraCalculo


class NormativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Normativa
        fields = (
            "id",
            "codigo",
            "nome",
            "referencia_portaria",
            "vigencia_inicio",
            "vigencia_fim",
            "situacao",
        )


class CompetenciaSerializer(serializers.ModelSerializer):
    normativa_codigo = serializers.CharField(source="normativa.codigo", read_only=True)

    class Meta:
        model = Competencia
        fields = ("id", "ano", "mes", "normativa", "normativa_codigo")


class IndicadorSerializer(serializers.ModelSerializer):
    pai_codigo = serializers.SerializerMethodField()
    normativa_codigo = serializers.CharField(source="normativa.codigo", read_only=True)

    def get_pai_codigo(self, indicador):
        if indicador.pai_id:
            return indicador.pai.codigo
        return ""

    class Meta:
        model = Indicador
        fields = (
            "id",
            "normativa",
            "normativa_codigo",
            "codigo",
            "nome",
            "nivel",
            "pai",
            "pai_codigo",
            "unidade_medida",
            "forma_calculo",
            "formula",
            "ativo",
        )


class RegraCalculoSerializer(serializers.ModelSerializer):
    indicador_codigo = serializers.CharField(source="indicador.codigo", read_only=True)
    peso_vigente = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = RegraCalculo
        fields = (
            "id",
            "indicador",
            "indicador_codigo",
            "cargo",
            "tipo_unidade",
            "abrangencia",
            "peso_portaria",
            "peso_excepcional",
            "peso_vigente",
            "meta",
        )
