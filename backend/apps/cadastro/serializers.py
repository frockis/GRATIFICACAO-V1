"""Saída da API no mesmo formato dos tipos do front (src/types/index.ts)."""
from rest_framework import serializers

from .models import Avaliado, Distrito, Unidade


class DistritoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distrito
        fields = ["id", "nome"]


class UnidadeSerializer(serializers.ModelSerializer):
    distritoId = serializers.CharField(source="distrito_id")

    class Meta:
        model = Unidade
        fields = ["id", "nome", "distritoId", "tipo", "cnes", "status"]


class UsuarioSerializer(serializers.ModelSerializer):
    """Avaliado no formato `Usuario` do front."""

    perfilId = serializers.CharField(source="perfil")
    unidadeId = serializers.CharField(source="unidade_id", allow_null=True)
    distritoId = serializers.CharField(source="distrito_id", allow_null=True)
    tipoUnidade = serializers.CharField(source="tipo_unidade", allow_null=True)

    class Meta:
        model = Avaliado
        fields = ["id", "nome", "email", "matricula", "perfilId", "unidadeId", "distritoId", "tipoUnidade", "status"]
