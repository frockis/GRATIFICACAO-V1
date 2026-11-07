"""Componente 'cadastro': Cadastro de Avaliados e Unidades.

Do plano de desenvolvimento:
- Define as classes 'Avaliado' e 'Unidade';
- Cadastra avaliados e unidades por JSON/https;
- Exibe o vínculo unidade-pessoa para 'apuração e homologação';
- Envia o que foi cadastrado para 'registro de auditoria'.

Os campos seguem os tipos do front (src/types/index.ts): Distrito, Unidade e
Usuario. Os ids são texto ("d1", "u1", "us1") para casar com os ids que o resto
do protótipo já usa (registros de indicadores, escopo etc.).
"""
import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class Status(models.TextChoices):
    ATIVO = "Ativo", "Ativo"
    INATIVO = "Inativo", "Inativo"


class TipoUnidade(models.TextChoices):
    USF = "USF", "USF"
    UBT = "UBT", "UBT"
    UPA = "UPA", "UPA"
    POLICLINICA = "Policlínica", "Policlínica"
    CAPS = "CAPS", "CAPS"
    OUTRO = "Outro", "Outro"


class PerfilId(models.TextChoices):
    """Mesmos ids de PerfilId no front."""

    GESTOR = "gestor", "Gestor de Unidade"
    COORDENADOR = "coordenador", "Coordenador Distrital"
    SEAB = "seab", "SEAB/CAM — Monitoramento"
    CONFIGURADOR = "configurador", "Configurador SAB"


# Perfis cuja gratificação é calculada (os demais só operam o sistema).
PERFIS_AVALIADOS = {PerfilId.GESTOR.value, PerfilId.COORDENADOR.value}


def proximo_id(modelo, prefixo: str) -> str:
    """Gera o próximo id no padrão do protótipo: d4, u5, us10..."""
    padrao = re.compile(rf"^{re.escape(prefixo)}(\d+)$")
    numeros = [int(m.group(1)) for i in modelo.objects.values_list("id", flat=True) if (m := padrao.match(i))]
    return f"{prefixo}{max(numeros, default=0) + 1}"


class ComIdTexto(models.Model):
    PREFIXO = ""

    id = models.CharField(primary_key=True, max_length=40, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = proximo_id(type(self), self.PREFIXO)
        super().save(*args, **kwargs)


class Distrito(ComIdTexto):
    PREFIXO = "d"

    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.nome


class Unidade(ComIdTexto):
    PREFIXO = "u"

    nome = models.CharField(max_length=200)
    distrito = models.ForeignKey(Distrito, on_delete=models.PROTECT, related_name="unidades")
    tipo = models.CharField(max_length=20, choices=TipoUnidade.choices)
    cnes = models.CharField(
        "CNES",
        max_length=7,
        unique=True,
        null=True,
        blank=True,
        validators=[RegexValidator(r"^\d{7}$", "O CNES deve ter 7 dígitos.")],
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ATIVO)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["distrito", "nome"], name="unidade_nome_unico_no_distrito")]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if self.cnes == "":
            self.cnes = None
        super().save(*args, **kwargs)

    def clean(self):
        self.nome = (self.nome or "").strip()
        if self.pk and self.distrito_id:
            anterior = Unidade.objects.filter(pk=self.pk).values_list("distrito_id", flat=True).first()
            if anterior and anterior != self.distrito_id and self.avaliados.exists():
                raise ValidationError(
                    {"distrito": "A unidade tem pessoas vinculadas. Mude o vínculo delas antes de trocar o distrito."}
                )


class Avaliado(ComIdTexto):
    """Pessoa cadastrada no SGGD com o seu vínculo atual (perfil + unidade/distrito).

    Corresponde ao tipo `Usuario` do front. Gestores de unidade e coordenadores
    distritais são os avaliados da gratificação; SEAB/CAM e Configurador também
    são cadastrados aqui porque usam o sistema, mas não entram no cálculo.
    Mudanças de vínculo ficam registradas na auditoria ("Vínculo alterado").
    """

    PREFIXO = "us"

    nome = models.CharField(max_length=200)
    email = models.EmailField("e-mail", unique=True)
    matricula = models.CharField("matrícula", max_length=20, unique=True, null=True, blank=True)
    perfil = models.CharField(max_length=20, choices=PerfilId.choices)
    unidade = models.ForeignKey(
        Unidade, on_delete=models.PROTECT, related_name="avaliados", null=True, blank=True
    )
    distrito = models.ForeignKey(
        Distrito, on_delete=models.PROTECT, related_name="avaliados", null=True, blank=True
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ATIVO)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.nome

    @property
    def tipo_unidade(self) -> str | None:
        return self.unidade.tipo if self.unidade_id else None

    @property
    def avaliado_na_gratificacao(self) -> bool:
        return self.perfil in PERFIS_AVALIADOS

    def save(self, *args, **kwargs):
        if self.matricula == "":
            self.matricula = None
        super().save(*args, **kwargs)

    def clean(self):
        """Mesmas regras de escopo do front (src/utils/escopo.ts)."""
        self.nome = (self.nome or "").strip()
        self.email = (self.email or "").strip().lower()
        erros = {}
        # Busca segura: se o id não existir, clean_fields() já reportou o erro do campo.
        unidade = Unidade.objects.filter(pk=self.unidade_id).first() if self.unidade_id else None
        if self.unidade_id and unidade is None:
            return

        if self.perfil == PerfilId.GESTOR:
            if unidade is None:
                erros["unidade"] = "Gestor de Unidade precisa estar vinculado a uma unidade."
            else:
                if self.distrito_id and self.distrito_id != unidade.distrito_id:
                    erros["distrito"] = "O distrito deve ser o mesmo da unidade."
                self.distrito_id = unidade.distrito_id
        elif self.perfil == PerfilId.COORDENADOR:
            if self.unidade_id:
                erros["unidade"] = "Coordenador Distrital é vinculado ao distrito, não a uma unidade."
            if not self.distrito_id:
                erros["distrito"] = "Coordenador Distrital precisa estar vinculado a um distrito."
        elif self.perfil in (PerfilId.SEAB, PerfilId.CONFIGURADOR):
            if self.unidade_id or self.distrito_id:
                erros["unidade"] = "Este perfil tem visão municipal e não é vinculado a unidade ou distrito."

        if unidade is not None and self.status == Status.ATIVO and unidade.status == Status.INATIVO:
            erros["unidade"] = "Não é possível vincular a uma unidade inativa."

        if erros:
            raise ValidationError(erros)
