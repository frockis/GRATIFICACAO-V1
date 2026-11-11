"""Contrato da normativa com apuração, coleta e o restante do time.

Este componente cadastra a normativa, a competência, os indicadores e as
regras de peso e meta. Não calcula pontuação (isso é da apuração) e não grava
resultado coletado (isso é da coleta).

Apuração e coleta importam só este módulo. A normativa, por sua vez, só chama
``apps.auditoria.interface.registrar`` ao gravar e ``apps.acesso.interface``
para saber se a pessoa pode cadastrar. Não importa coleta, apuração, cadastro,
pagamento, publicação nem recurso.

O que mostrar na apresentação:

- Indicador e Competencia são as classes deste app. Normativa é a versão da
  portaria (CAM 1.2, CAM 2.0). RegraCalculo guarda peso da portaria, peso
  excepcional e meta por cargo e tipo de unidade.
- A competência amarra o mês à versão que vale naquele mês. Trocar a portaria
  não altera mês já cadastrado. Encerrar o ciclo continua na apuração.
- ``regras_para_apuracao`` entrega peso vigente, meta e a orientação de cálculo.
  Peso vigente é o excepcional, se existir (inclusive zero); senão, o da portaria.
- ``indicadores_para_coleta`` entrega o que a unidade preenche, com o pai e os
  filhos, para o cargo e o tipo de unidade pedidos.
- A soma dos pesos de primeiro nível é só uma conferência. O peso do
  subindicador compõe a nota do pai e não entra de novo nessa soma.
- O arquivo ``exemplo_indicadores.csv`` é um modelo. Os percentuais 20, 20, 20
  e 40 repetem a leitura do resultado geral da planilha anonimizada para USF;
  o peso excepcional do SnB2 está no arquivo para demonstrar a substituição.
  A planilha não foi carregada inteira: o PDF não preserva a coluna de cada
  unidade. Confirme na planilha antes de tratar qualquer número como oficial.
"""

from dataclasses import asdict, dataclass
from decimal import Decimal

from .models import ORIENTACAO_CALCULO, Competencia, Indicador, RegraCalculo


class CompetenciaNaoCadastrada(LookupError):
    """Não há competência para o mês pedido. A apuração e a coleta tratam este caso."""

    def __init__(self, ano, mes):
        self.ano = ano
        self.mes = mes
        super().__init__(f"Não há competência cadastrada para {mes:02d}/{ano}.")


@dataclass(frozen=True)
class RegraParaApuracao:
    normativa_codigo: str
    competencia_ano: int
    competencia_mes: int
    indicador_id: int
    indicador_codigo: str
    indicador_nome: str
    indicador_pai_codigo: str
    nivel: str
    forma_calculo: str
    orientacao_calculo: str
    formula: str
    unidade_medida: str
    cargo: str
    tipo_unidade: str
    abrangencia: str
    peso_portaria: Decimal
    peso_excepcional: Decimal | None
    peso_vigente: Decimal
    meta: Decimal | None

    def para_dict(self):
        return _numeros_como_texto(asdict(self))


@dataclass(frozen=True)
class IndicadorParaColeta:
    normativa_codigo: str
    competencia_ano: int
    competencia_mes: int
    indicador_id: int
    codigo: str
    nome: str
    pai_codigo: str
    nivel: str
    unidade_medida: str
    formula: str
    forma_calculo: str
    cargo: str
    tipo_unidade: str
    meta: Decimal | None

    def para_dict(self):
        return _numeros_como_texto(asdict(self))


def regras_para_apuracao(*, ano, mes, cargo="", tipo_unidade=""):
    """Regras de cálculo da competência, para a apuração homologar.

    Sem cargo e sem tipo de unidade, devolve todas as regras. Com filtro, fica
    uma regra por indicador: a mais específica que serve para aquele cargo e
    tipo. Campo vazio na regra vale para qualquer um daquele eixo.
    """
    competencia = _competencia(ano, mes)
    regras = _regras_da(competencia)
    if not cargo and not tipo_unidade:
        escolhidas = regras
    else:
        escolhidas = _mais_especificas(regras, cargo, tipo_unidade)
    return [_regra_consulta(competencia, regra) for regra in _ordenar_regras(escolhidas)]


def indicadores_para_coleta(*, ano, mes, cargo="", tipo_unidade=""):
    """Indicadores que a coleta preenche nessa competência.

    Com cargo ou tipo de unidade, entram os indicadores que têm regra
    compatível e também o pai e os filhos, para a tela montar a árvore.
    A meta vem da regra mais específica. Sem filtro, a meta só aparece quando
    o indicador tem uma única regra.
    """
    competencia = _competencia(ano, mes)
    indicadores = list(
        Indicador.objects.filter(normativa=competencia.normativa, ativo=True).select_related("pai")
    )
    por_id = {item.id: item for item in indicadores}
    filhos = {}
    for item in indicadores:
        filhos.setdefault(item.pai_id, []).append(item)
    regras = _regras_da(competencia)

    if not cargo and not tipo_unidade:
        meta_por_indicador = _meta_unica(regras)
        escolhidos = indicadores
        cargo_por_indicador = {}
        tipo_por_indicador = {}
    else:
        especificas = _mais_especificas(regras, cargo, tipo_unidade)
        sementes = {regra.indicador_id for regra in especificas}
        escolhidos = _com_familia(sementes, por_id, filhos)
        meta_por_indicador = {regra.indicador_id: regra.meta for regra in especificas}
        cargo_por_indicador = {regra.indicador_id: regra.cargo for regra in especificas}
        tipo_por_indicador = {regra.indicador_id: regra.tipo_unidade for regra in especificas}

    return [
        IndicadorParaColeta(
            normativa_codigo=competencia.normativa.codigo,
            competencia_ano=competencia.ano,
            competencia_mes=competencia.mes,
            indicador_id=item.id,
            codigo=item.codigo,
            nome=item.nome,
            pai_codigo=item.pai.codigo if item.pai_id else "",
            nivel=item.nivel,
            unidade_medida=item.unidade_medida,
            formula=item.formula,
            forma_calculo=item.forma_calculo,
            cargo=cargo_por_indicador.get(item.id, ""),
            tipo_unidade=tipo_por_indicador.get(item.id, ""),
            meta=meta_por_indicador.get(item.id),
        )
        for item in sorted(escolhidos, key=lambda item: _chave_codigo(item.codigo))
    ]


def soma_pesos_de_primeiro_nivel(regras):
    """Soma o peso vigente só dos indicadores de primeiro nível.

    O subindicador explica a nota do pai. Somá-lo de novo contaria o mesmo
    eixo duas vezes na gratificação. Passe a lista já filtrada por cargo e
    tipo de unidade; sem filtro, o mesmo indicador pode entrar mais de uma vez.
    """
    return sum(
        (regra.peso_vigente for regra in regras if regra.nivel == "indicador"),
        Decimal("0"),
    )


def _competencia(ano, mes):
    try:
        return Competencia.objects.select_related("normativa").get(ano=int(ano), mes=int(mes))
    except (Competencia.DoesNotExist, TypeError, ValueError):
        raise CompetenciaNaoCadastrada(ano, mes) from None


def _regras_da(competencia):
    return list(
        RegraCalculo.objects.filter(
            indicador__normativa=competencia.normativa,
            indicador__ativo=True,
        ).select_related("indicador", "indicador__pai", "indicador__normativa")
    )


def _compativel(regra, cargo, tipo_unidade):
    if cargo and regra.cargo and regra.cargo.casefold() != cargo.casefold():
        return False
    if tipo_unidade and regra.tipo_unidade and regra.tipo_unidade.casefold() != tipo_unidade.casefold():
        return False
    return True


def _especificidade(regra):
    return (2 if regra.cargo else 0) + (1 if regra.tipo_unidade else 0)


def _mais_especificas(regras, cargo, tipo_unidade):
    melhores = {}
    for regra in regras:
        if not _compativel(regra, cargo, tipo_unidade):
            continue
        atual = melhores.get(regra.indicador_id)
        if atual is None or _especificidade(regra) > _especificidade(atual):
            melhores[regra.indicador_id] = regra
    return list(melhores.values())


def _com_familia(sementes, por_id, filhos):
    escolhidos = set()

    def subir(item):
        while item is not None and item.id not in escolhidos:
            escolhidos.add(item.id)
            item = por_id.get(item.pai_id)

    def descer(item_id):
        for filho in filhos.get(item_id, []):
            if filho.id not in escolhidos:
                escolhidos.add(filho.id)
                descer(filho.id)

    for item_id in sementes:
        item = por_id.get(item_id)
        if item is None:
            continue
        subir(item)
        descer(item.id)
    return [por_id[item_id] for item_id in escolhidos]


def _meta_unica(regras):
    grupos = {}
    for regra in regras:
        grupos.setdefault(regra.indicador_id, []).append(regra)
    metas = {}
    for indicador_id, do_indicador in grupos.items():
        if len(do_indicador) == 1:
            metas[indicador_id] = do_indicador[0].meta
    return metas


def _regra_consulta(competencia, regra):
    indicador = regra.indicador
    return RegraParaApuracao(
        normativa_codigo=competencia.normativa.codigo,
        competencia_ano=competencia.ano,
        competencia_mes=competencia.mes,
        indicador_id=indicador.id,
        indicador_codigo=indicador.codigo,
        indicador_nome=indicador.nome,
        indicador_pai_codigo=indicador.pai.codigo if indicador.pai_id else "",
        nivel=indicador.nivel,
        forma_calculo=indicador.forma_calculo,
        orientacao_calculo=ORIENTACAO_CALCULO[indicador.forma_calculo],
        formula=indicador.formula,
        unidade_medida=indicador.unidade_medida,
        cargo=regra.cargo,
        tipo_unidade=regra.tipo_unidade,
        abrangencia=regra.abrangencia,
        peso_portaria=regra.peso_portaria,
        peso_excepcional=regra.peso_excepcional,
        peso_vigente=regra.peso_vigente,
        meta=regra.meta,
    )


def _ordenar_regras(regras):
    return sorted(regras, key=lambda regra: (_chave_codigo(regra.indicador.codigo), regra.cargo, regra.tipo_unidade))


def _chave_codigo(codigo):
    partes = []
    for pedaco in codigo.split("."):
        if pedaco.isdigit():
            partes.append((0, int(pedaco), ""))
        else:
            partes.append((1, 0, pedaco.casefold()))
    return partes


def _numeros_como_texto(dados):
    convertidos = {}
    for chave, valor in dados.items():
        if isinstance(valor, Decimal):
            convertidos[chave] = format(valor, "f")
        else:
            convertidos[chave] = valor
    return convertidos
