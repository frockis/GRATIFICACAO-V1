"""Classes da normativa da gratificação por desempenho da SESAU.

Indicador e Competencia são as duas classes pedidas para este componente.
Normativa é a versão da portaria (ex.: CAM 1.2) e RegraCalculo é o peso e a
meta daquele indicador para um cargo e um tipo de unidade.

A planilha anonimizada (atualizada em 10/02/2025) organiza o catálogo assim:
indicador, subindicador e sub-subindicador; peso da portaria e peso atual
excepcional; cargos de coordenação de unidade (SEAB/SERMAC) e cargos de
distrito (GG, SnA, SnB1, SnB2); tipos de unidade como USF, UBT, CAPS, CECON,
UCIS e MAC.

Encerrar o ciclo do mês não é daqui: a permissão encerrar_ciclo é da apuração.
A competência só amarra o mês à versão da normativa que vale naquele mês, para
uma portaria nova não reescrever período já cadastrado.
"""

from calendar import monthrange
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SituacaoNormativa(models.TextChoices):
    VIGENTE = "vigente", "Vigente"
    ENCERRADA = "encerrada", "Encerrada"


class NivelIndicador(models.TextChoices):
    INDICADOR = "indicador", "Indicador"
    SUBINDICADOR = "subindicador", "Subindicador"
    SUB_SUBINDICADOR = "sub_subindicador", "Sub-subindicador"


class FormaCalculo(models.TextChoices):
    PROPORCAO = "proporcao", "Proporção do realizado sobre a meta"
    MEDIA_SUBINDICADORES = "media_subindicadores", "Média das notas dos subindicadores"
    NOTA_INFORMADA = "nota_informada", "Nota de atingimento informada (0 a 100)"


# Texto estável para a apuração aplicar a regra sem reimplementar a leitura da portaria.
ORIENTACAO_CALCULO = {
    FormaCalculo.PROPORCAO: (
        "Pontos = mínimo(valor informado / meta, 1) × peso vigente. "
        "Valor e meta na mesma unidade. Sem meta, a apuração não calcula."
    ),
    FormaCalculo.MEDIA_SUBINDICADORES: (
        "Nota = média das notas dos subindicadores, de 0 a 100. "
        "Se este indicador tiver peso, pontos = (nota / 100) × peso vigente."
    ),
    FormaCalculo.NOTA_INFORMADA: (
        "O valor coletado já é o atingimento de 0 a 100. "
        "Pontos = (valor / 100) × peso vigente."
    ),
}

NIVEL_DO_PAI = {
    NivelIndicador.SUBINDICADOR: NivelIndicador.INDICADOR,
    NivelIndicador.SUB_SUBINDICADOR: NivelIndicador.SUBINDICADOR,
}

_VALIDADOR_PESO = [
    MinValueValidator(0, message="O peso não pode ser negativo."),
    MaxValueValidator(100, message="O peso não pode passar de 100."),
]


class Normativa(models.Model):
    """Versão da portaria que define indicadores, pesos e metas."""

    codigo = models.CharField(max_length=40, unique=True)
    nome = models.CharField(max_length=200)
    referencia_portaria = models.CharField(
        max_length=200,
        blank=True,
        help_text="Identificação da portaria. O peso excepcional pode se afastar dela.",
    )
    vigencia_inicio = models.DateField()
    vigencia_fim = models.DateField(null=True, blank=True)
    situacao = models.CharField(
        max_length=16,
        choices=SituacaoNormativa.choices,
        default=SituacaoNormativa.VIGENTE,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "normativa"
        verbose_name_plural = "normativas"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} — {self.nome}"

    def clean(self):
        if self.vigencia_fim and self.vigencia_inicio and self.vigencia_fim < self.vigencia_inicio:
            raise ValidationError(
                {"vigencia_fim": "O fim da vigência não pode ser anterior ao início."}
            )

    def cobre(self, ano, mes):
        """Diz se algum dia do mês informado cai dentro da vigência."""
        inicio_mes = date(ano, mes, 1)
        ultimo = date(ano, mes, monthrange(ano, mes)[1])
        if ultimo < self.vigencia_inicio:
            return False
        if self.vigencia_fim and inicio_mes > self.vigencia_fim:
            return False
        return True


class Competencia(models.Model):
    """Mês de referência da gratificação e a normativa que vale nesse mês."""

    ano = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    normativa = models.ForeignKey(Normativa, on_delete=models.PROTECT, related_name="competencias")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "competência"
        verbose_name_plural = "competências"
        ordering = ["-ano", "-mes"]
        constraints = [
            models.UniqueConstraint(fields=["ano", "mes"], name="competencia_unica_por_mes"),
        ]

    def __str__(self):
        return f"{self.mes:02d}/{self.ano} — {self.normativa.codigo}"

    def clean(self):
        if self.mes < 1 or self.mes > 12:
            raise ValidationError({"mes": "O mês fica entre 1 e 12."})
        if self.ano < 2000 or self.ano > 2100:
            raise ValidationError({"ano": "Informe um ano entre 2000 e 2100."})
        if self.normativa_id and not self.normativa.cobre(self.ano, self.mes):
            raise ValidationError(
                {"normativa": "Essa competência está fora da vigência da normativa."}
            )


class Indicador(models.Model):
    """Indicador, subindicador ou sub-subindicador de uma normativa."""

    normativa = models.ForeignKey(Normativa, on_delete=models.PROTECT, related_name="indicadores")
    codigo = models.CharField(max_length=40)
    nome = models.CharField(max_length=500)
    nivel = models.CharField(
        max_length=20,
        choices=NivelIndicador.choices,
        default=NivelIndicador.INDICADOR,
    )
    pai = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="filhos",
    )
    unidade_medida = models.CharField(max_length=40, default="%")
    forma_calculo = models.CharField(
        max_length=32,
        choices=FormaCalculo.choices,
        default=FormaCalculo.PROPORCAO,
    )
    formula = models.TextField(
        blank=True,
        help_text="Descrição de como o valor é obtido, como está na portaria ou na planilha.",
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "indicador"
        verbose_name_plural = "indicadores"
        ordering = ["normativa_id", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["normativa", "codigo"],
                name="indicador_unico_na_normativa",
            ),
        ]

    def __str__(self):
        return f"{self.codigo} {self.nome}"

    def clean(self):
        if self.nivel == NivelIndicador.INDICADOR:
            if self.pai_id:
                raise ValidationError({"pai": "Indicador de primeiro nível não tem pai."})
            return
        if not self.pai_id:
            raise ValidationError({"pai": "Informe o indicador pai."})
        pai = self.pai
        if pai.normativa_id != self.normativa_id:
            raise ValidationError({"pai": "O pai precisa ser da mesma normativa."})
        if self.pk and pai.pk == self.pk:
            raise ValidationError({"pai": "O indicador não pode ser pai dele mesmo."})
        esperado = NIVEL_DO_PAI[self.nivel]
        if pai.nivel != esperado:
            raise ValidationError({"pai": f"O pai precisa ser do nível {esperado}."})
        visto = set()
        atual = pai
        while atual is not None:
            if atual.pk in visto or (self.pk and atual.pk == self.pk):
                raise ValidationError({"pai": "A hierarquia do indicador não pode formar um ciclo."})
            visto.add(atual.pk)
            atual = atual.pai


class RegraCalculo(models.Model):
    """Peso e meta de um indicador para um cargo e um tipo de unidade.

    O peso vigente é o excepcional, quando existe; senão, o da portaria.
    Cargo ou tipo em branco significa que a regra vale para todos desse eixo.
    """

    indicador = models.ForeignKey(Indicador, on_delete=models.PROTECT, related_name="regras")
    cargo = models.CharField(
        max_length=80,
        blank=True,
        help_text="Ex.: coordenador_us, gg, sna, snb1, snb2. Vazio vale para qualquer cargo.",
    )
    tipo_unidade = models.CharField(
        max_length=40,
        blank=True,
        help_text="Ex.: USF, UBT, UBT MISTA, CAPS, CECON, UCIS, MAC. Vazio vale para qualquer tipo.",
    )
    abrangencia = models.TextField(
        blank=True,
        help_text="Texto da coluna 'aferido para os cargos' da planilha, quando houver.",
    )
    peso_portaria = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=_VALIDADOR_PESO,
    )
    peso_excepcional = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=_VALIDADOR_PESO,
        help_text="Quando preenchido, inclusive zero, substitui o peso da portaria.",
    )
    meta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0, message="A meta não pode ser negativa.")],
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "regra de cálculo"
        verbose_name_plural = "regras de cálculo"
        ordering = ["indicador_id", "cargo", "tipo_unidade"]
        constraints = [
            models.UniqueConstraint(
                fields=["indicador", "cargo", "tipo_unidade"],
                name="regra_unica_por_cargo_e_unidade",
            ),
        ]

    def __str__(self):
        destino = self.cargo or self.tipo_unidade or "geral"
        return f"{self.indicador.codigo} / {destino}"

    @property
    def peso_vigente(self):
        if self.peso_excepcional is not None:
            return self.peso_excepcional
        return self.peso_portaria
