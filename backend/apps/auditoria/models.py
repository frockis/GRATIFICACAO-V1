from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    """Rastro do que os componentes cadastram ou alteram.

    A normativa grava aqui cada normativa, competência, indicador e regra.
    O registro é só inclusão: a tela de consulta do histórico continua
    responsabilidade deste componente, em cima destes dados.
    """

    ocorrido_em = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="registros_de_auditoria",
    )
    # Nome de usuário no momento do fato. O cadastro da pessoa pode mudar depois.
    usuario_identificacao = models.CharField(max_length=150, blank=True)
    operacao = models.CharField(max_length=64)
    entidade = models.CharField(max_length=64)
    identificador = models.CharField(max_length=120)
    valor_anterior = models.TextField(blank=True)
    valor_novo = models.TextField(blank=True)

    class Meta:
        verbose_name = "registro de auditoria"
        verbose_name_plural = "registros de auditoria"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["entidade", "identificador"], name="auditoria_entidade_id_idx"),
        ]

    def __str__(self):
        return f"{self.operacao} {self.entidade} {self.identificador}"
