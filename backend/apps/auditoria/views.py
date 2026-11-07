from django.utils import timezone
from rest_framework import mixins, serializers, viewsets

from .models import RegistroAuditoria


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    """Mesmo formato de AuditoriaEntrada (front)."""

    id = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    horario = serializers.SerializerMethodField()
    registroAfetado = serializers.CharField(source="registro_afetado")
    valorAnterior = serializers.CharField(source="valor_anterior")
    novoValor = serializers.CharField(source="novo_valor")

    class Meta:
        model = RegistroAuditoria
        fields = [
            "id",
            "usuario",
            "data",
            "horario",
            "operacao",
            "registroAfetado",
            "valorAnterior",
            "novoValor",
            "perfil",
            "localizacao",
            "componente",
        ]

    def get_id(self, obj) -> str:
        return f"api-aud-{obj.pk}"

    def get_data(self, obj) -> str:
        return timezone.localtime(obj.data_hora).strftime("%d/%m/%Y")

    def get_horario(self, obj) -> str:
        return timezone.localtime(obj.data_hora).strftime("%H:%M")


class RegistroAuditoriaViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """GET /api/auditoria/?componente=cadastro"""

    serializer_class = RegistroAuditoriaSerializer

    def get_queryset(self):
        qs = RegistroAuditoria.objects.all()
        if componente := self.request.query_params.get("componente"):
            qs = qs.filter(componente=componente)
        return qs[:500]
