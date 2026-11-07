"""Registro de Auditoria (base mínima).

Segue o plano: cada componente chama `auditoria.services.registrar(...)` ao
fazer uma operação. Os campos espelham AuditoriaEntrada do front
(src/types/index.ts), para a tela de Auditoria mostrar sem conversão.

Registros não são editados nem apagados (ver admin.py).
"""
from django.db import models


class RegistroAuditoria(models.Model):
    data_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    componente = models.CharField(max_length=30, help_text="App que gerou o registro (ex.: cadastro).")
    usuario = models.CharField(max_length=200)
    perfil = models.CharField(max_length=60, blank=True)
    operacao = models.CharField(max_length=100)
    registro_afetado = models.CharField(max_length=300)
    valor_anterior = models.TextField(blank=True)
    novo_valor = models.TextField(blank=True)
    localizacao = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "registro de auditoria"
        verbose_name_plural = "registros de auditoria"
        ordering = ["-data_hora", "-id"]

    def __str__(self):
        return f"{self.data_hora:%d/%m/%Y %H:%M} · {self.operacao} · {self.registro_afetado}"
