"""Cadastro de normativas, competências, indicadores e regras.

Permissões já definidas no controle de acesso (o catálogo não foi ampliado):

- ``acesso.cadastrar_indicador`` grava normativa, competência e indicador.
- ``acesso.configurar_regra_calculo`` grava peso, meta e abrangência.
- A importação em massa exige as duas, porque o arquivo traz os dois.

Cada gravação chama ``apps.auditoria.interface.registrar``. O campo
``entidade`` distingue normativa, competência, indicador e regra; a operação
no rastro diz o que foi feito.
"""

import csv
import json
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.acesso.interface import usuario_tem_permissao
from apps.auditoria.interface import registrar

from .models import (
    NIVEL_DO_PAI,
    Competencia,
    FormaCalculo,
    Indicador,
    NivelIndicador,
    Normativa,
    RegraCalculo,
    SituacaoNormativa,
)

PERMISSAO_INDICADOR = "acesso.cadastrar_indicador"
PERMISSAO_REGRA = "acesso.configurar_regra_calculo"

_ALIAS_COLUNA = {
    "codigo": "codigo",
    "nome": "nome",
    "nivel": "nivel",
    "codigo_pai": "codigo_pai",
    "pai": "codigo_pai",
    "unidade_medida": "unidade_medida",
    "unidade": "unidade_medida",
    "forma_calculo": "forma_calculo",
    "formula": "formula",
    "abrangencia": "abrangencia",
    "cargo": "cargo",
    "tipo_unidade": "tipo_unidade",
    "peso_portaria": "peso_portaria",
    "peso": "peso_portaria",
    "peso_excepcional": "peso_excepcional",
    "meta": "meta",
}

_CAMPOS_DO_INDICADOR = (
    "nome",
    "nivel",
    "codigo_pai",
    "unidade_medida",
    "forma_calculo",
    "formula",
)
_CAMPOS_DE_REGRA = (
    "cargo",
    "tipo_unidade",
    "abrangencia",
    "peso_portaria",
    "peso_excepcional",
    "meta",
)


def cadastrar_normativa(usuario, dados):
    _exige(usuario, PERMISSAO_INDICADOR)
    dados = _mapa(dados)
    with transaction.atomic():
        normativa = Normativa(
            codigo=_texto(dados.get("codigo"), "codigo"),
            nome=_texto(dados.get("nome"), "nome"),
            referencia_portaria=_texto(dados.get("referencia_portaria"), obrigatorio=False),
            vigencia_inicio=_data(dados.get("vigencia_inicio"), "vigencia_inicio"),
            vigencia_fim=_data(dados.get("vigencia_fim"), "vigencia_fim", obrigatorio=False),
            situacao=_escolha(
                dados.get("situacao") or SituacaoNormativa.VIGENTE,
                SituacaoNormativa.values,
                "situacao",
            ),
        )
        if Normativa.objects.filter(codigo=normativa.codigo).exists():
            raise ValidationError({"codigo": "Já existe normativa com este código."})
        _salvar(normativa)
        _auditar(usuario, "cadastrar_normativa", "normativa", normativa.codigo, "", _foto_normativa(normativa))
        return normativa


def cadastrar_competencia(usuario, dados):
    _exige(usuario, PERMISSAO_INDICADOR)
    dados = _mapa(dados)
    with transaction.atomic():
        normativa = _normativa_por_id(dados.get("normativa") or dados.get("normativa_id"))
        ano = _inteiro(dados.get("ano"), "ano")
        mes = _inteiro(dados.get("mes"), "mes")
        if Competencia.objects.filter(ano=ano, mes=mes).exists():
            raise ValidationError({"mes": "Já existe competência para esse mês."})
        competencia = Competencia(ano=ano, mes=mes, normativa=normativa)
        _salvar(competencia)
        _auditar(
            usuario,
            "cadastrar_competencia",
            "competencia",
            f"{ano}-{mes:02d}",
            "",
            _foto_competencia(competencia),
        )
        return competencia


def cadastrar_indicador(usuario, dados):
    _exige(usuario, PERMISSAO_INDICADOR)
    dados = _mapa(dados)
    with transaction.atomic():
        indicador = _montar_indicador(dados)
        _salvar(indicador)
        _auditar(
            usuario,
            "cadastrar_indicador",
            "indicador",
            _id_indicador(indicador),
            "",
            _foto_indicador(indicador),
        )
        return indicador


def atualizar_indicador(usuario, indicador_id, dados):
    _exige(usuario, PERMISSAO_INDICADOR)
    dados = _mapa(dados)
    with transaction.atomic():
        indicador = Indicador.objects.select_related("normativa", "pai").get(pk=indicador_id)
        anterior = _foto_indicador(indicador)
        if "codigo" in dados:
            indicador.codigo = _texto(dados.get("codigo"), "codigo")
        if "nome" in dados:
            indicador.nome = _texto(dados.get("nome"), "nome")
        if "nivel" in dados:
            indicador.nivel = _escolha(dados.get("nivel"), NivelIndicador.values, "nivel")
        if "unidade_medida" in dados:
            indicador.unidade_medida = _texto(dados.get("unidade_medida"), "unidade_medida") or "%"
        if "forma_calculo" in dados:
            indicador.forma_calculo = _escolha(dados.get("forma_calculo"), FormaCalculo.values, "forma_calculo")
        if "formula" in dados:
            indicador.formula = _texto(dados.get("formula"), obrigatorio=False)
        if "ativo" in dados:
            indicador.ativo = _booleano(dados.get("ativo"))
        if "pai" in dados or "codigo_pai" in dados:
            indicador.pai = _pai_informado(indicador.normativa, dados, indicador.nivel)
        if Indicador.objects.filter(normativa=indicador.normativa, codigo=indicador.codigo).exclude(pk=indicador.pk).exists():
            raise ValidationError({"codigo": "Já existe indicador com este código nesta normativa."})
        _salvar(indicador)
        _auditar(
            usuario,
            "atualizar_indicador",
            "indicador",
            _id_indicador(indicador),
            anterior,
            _foto_indicador(indicador),
        )
        return indicador


def configurar_regra(usuario, dados):
    """Cria ou atualiza a regra do indicador para o mesmo cargo e tipo de unidade."""
    _exige(usuario, PERMISSAO_REGRA)
    dados = _mapa(dados)
    with transaction.atomic():
        indicador = _indicador_por_referencia(dados)
        cargo = _texto(dados.get("cargo"), obrigatorio=False)
        tipo_unidade = _texto(dados.get("tipo_unidade"), obrigatorio=False)
        regra = RegraCalculo.objects.filter(
            indicador=indicador,
            cargo=cargo,
            tipo_unidade=tipo_unidade,
        ).first()
        anterior = _foto_regra(regra) if regra else ""
        if regra is None:
            regra = RegraCalculo(indicador=indicador, cargo=cargo, tipo_unidade=tipo_unidade)
        _preencher_regra(regra, dados)
        _salvar(regra)
        _auditar(
            usuario,
            "configurar_regra_calculo",
            "regra_calculo",
            _id_regra(regra),
            anterior,
            _foto_regra(regra),
        )
        return regra


def importar_indicadores(usuario, normativa_id, conteudo):
    """Cadastra indicadores e regras a partir de um CSV.

    Separador ``;`` ou ``,``. Cabeçalho na primeira linha. Colunas reconhecidas:
    codigo, nome, nivel, codigo_pai, unidade_medida, forma_calculo, formula,
    abrangencia, cargo, tipo_unidade, peso_portaria, peso_excepcional, meta.

    O mesmo código em várias linhas é um indicador com várias regras (uma por
    cargo e tipo de unidade). O pai precisa existir antes do filho. Se alguma
    linha falha, nada é gravado.
    """
    _exige(usuario, PERMISSAO_INDICADOR)
    _exige(usuario, PERMISSAO_REGRA)
    texto = (conteudo or "").lstrip("\ufeff").strip()
    if not texto:
        raise ValidationError({"arquivo": "O arquivo está vazio."})

    normativa = _normativa_por_id(normativa_id)
    linhas = _ler_csv(texto)
    grupos, erros = _agrupar_linhas(linhas)
    if erros:
        raise ValidationError({"arquivo": erros})

    with transaction.atomic():
        indicadores = _gravar_grupos(usuario, normativa, grupos)
        return indicadores


def _gravar_grupos(usuario, normativa, grupos):
    existentes = {item.codigo: item for item in Indicador.objects.filter(normativa=normativa)}
    gravados = []
    for codigo, grupo in grupos.items():
        indicador = existentes.get(codigo)
        if indicador is None:
            indicador = _montar_indicador(
                {
                    "normativa": normativa.id,
                    "codigo": codigo,
                    "nome": grupo["nome"],
                    "nivel": grupo["nivel"],
                    "codigo_pai": grupo["codigo_pai"],
                    "unidade_medida": grupo["unidade_medida"],
                    "forma_calculo": grupo["forma_calculo"],
                    "formula": grupo["formula"],
                },
                conhecidos=existentes,
            )
            _salvar(indicador)
            _auditar(
                usuario,
                "cadastrar_indicador",
                "indicador",
                _id_indicador(indicador),
                "",
                _foto_indicador(indicador),
            )
            existentes[codigo] = indicador
        else:
            anterior = _foto_indicador(indicador)
            indicador.nome = grupo["nome"]
            indicador.nivel = grupo["nivel"]
            indicador.unidade_medida = grupo["unidade_medida"]
            indicador.forma_calculo = grupo["forma_calculo"]
            indicador.formula = grupo["formula"]
            indicador.pai = _resolver_pai(normativa, grupo["codigo_pai"], grupo["nivel"], existentes)
            _salvar(indicador)
            _auditar(
                usuario,
                "atualizar_indicador",
                "indicador",
                _id_indicador(indicador),
                anterior,
                _foto_indicador(indicador),
            )
        for regra_dados in grupo["regras"]:
            configurar_regra(
                usuario,
                {
                    "indicador": indicador.id,
                    "cargo": regra_dados["cargo"],
                    "tipo_unidade": regra_dados["tipo_unidade"],
                    "abrangencia": regra_dados["abrangencia"],
                    "peso_portaria": regra_dados["peso_portaria"],
                    "peso_excepcional": regra_dados["peso_excepcional"],
                    "meta": regra_dados["meta"],
                },
            )
        gravados.append(indicador)
    return gravados


def _agrupar_linhas(linhas):
    grupos = {}
    erros = []
    vistos_regra = set()
    for numero, linha in linhas:
        codigo = _celula(linha.get("codigo"))
        if not codigo:
            erros.append(f"Linha {numero}: informe o código do indicador.")
            continue
        grupo = grupos.get(codigo)
        if grupo is None:
            nome = _celula(linha.get("nome"))
            if not nome:
                erros.append(f"Linha {numero}: informe o nome do indicador {codigo}.")
                continue
            nivel = _celula(linha.get("nivel")) or (
                NivelIndicador.SUBINDICADOR if _celula(linha.get("codigo_pai")) else NivelIndicador.INDICADOR
            )
            if nivel not in NivelIndicador.values:
                erros.append(f"Linha {numero}: nível '{nivel}' não é indicador, subindicador ou sub_subindicador.")
                continue
            forma = _celula(linha.get("forma_calculo")) or FormaCalculo.PROPORCAO
            if forma not in FormaCalculo.values:
                erros.append(
                    f"Linha {numero}: forma de cálculo '{forma}' não é "
                    "proporcao, media_subindicadores ou nota_informada."
                )
                continue
            grupo = {
                "nome": nome,
                "nivel": nivel,
                "codigo_pai": _celula(linha.get("codigo_pai")),
                "unidade_medida": _celula(linha.get("unidade_medida")) or "%",
                "forma_calculo": forma,
                "formula": _celula(linha.get("formula")),
                "regras": [],
                "linha": numero,
            }
            grupos[codigo] = grupo
        else:
            _conferir_repeticao(numero, codigo, linha, grupo, erros)

        if _linha_tem_regra(linha):
            peso = _celula(linha.get("peso_portaria"))
            if not peso:
                erros.append(f"Linha {numero}: a regra do indicador {codigo} precisa do peso da portaria.")
                continue
            cargo = _celula(linha.get("cargo"))
            tipo_unidade = _celula(linha.get("tipo_unidade"))
            chave = (codigo, cargo.casefold(), tipo_unidade.casefold())
            if chave in vistos_regra:
                erros.append(
                    f"Linha {numero}: regra repetida para {codigo}, cargo '{cargo or 'todos'}' "
                    f"e tipo '{tipo_unidade or 'todos'}'."
                )
                continue
            vistos_regra.add(chave)
            regra = {
                "cargo": cargo,
                "tipo_unidade": tipo_unidade,
                "abrangencia": _celula(linha.get("abrangencia")),
                "peso_portaria": peso,
                "peso_excepcional": _celula(linha.get("peso_excepcional")),
                "meta": _celula(linha.get("meta")),
            }
            erros.extend(_erros_de_regra(numero, codigo, regra))
            grupo["regras"].append(regra)

    ordem = list(grupos)
    for codigo, grupo in grupos.items():
        pai = grupo["codigo_pai"]
        if grupo["nivel"] == NivelIndicador.INDICADOR and pai:
            erros.append(f"Linha {grupo['linha']}: o indicador {codigo} é de primeiro nível e não tem pai.")
        if grupo["nivel"] != NivelIndicador.INDICADOR and not pai:
            erros.append(f"Linha {grupo['linha']}: informe o código pai de {codigo}.")
        if pai and pai in grupos and ordem.index(pai) > ordem.index(codigo):
            erros.append(f"Linha {grupo['linha']}: coloque o indicador pai '{pai}' antes de {codigo}.")
        if pai and pai in grupos and grupo["nivel"] in NIVEL_DO_PAI:
            if grupos[pai]["nivel"] != NIVEL_DO_PAI[grupo["nivel"]]:
                erros.append(
                    f"Linha {grupo['linha']}: o pai '{pai}' de {codigo} precisa ser do nível "
                    f"{NIVEL_DO_PAI[grupo['nivel']]}."
                )
    return grupos, erros


def _erros_de_regra(numero, codigo, regra):
    erros = []
    for campo, obrigatorio, teto in (
        ("peso_portaria", True, Decimal("100")),
        ("peso_excepcional", False, Decimal("100")),
        ("meta", False, None),
    ):
        valor = regra[campo]
        if valor in ("", None):
            continue
        try:
            numero_decimal = _decimal(valor, campo, obrigatorio=obrigatorio)
        except ValidationError:
            erros.append(f"Linha {numero}: o campo {campo} do indicador {codigo} não é um número.")
            continue
        if numero_decimal < 0 or (teto is not None and numero_decimal > teto):
            limite = "entre 0 e 100" if teto is not None else "zero ou mais"
            erros.append(f"Linha {numero}: o campo {campo} do indicador {codigo} precisa ser {limite}.")
    return erros


def _conferir_repeticao(numero, codigo, linha, grupo, erros):
    comparacoes = {
        "nome": grupo["nome"],
        "nivel": grupo["nivel"],
        "codigo_pai": grupo["codigo_pai"],
        "unidade_medida": grupo["unidade_medida"],
        "forma_calculo": grupo["forma_calculo"],
        "formula": grupo["formula"],
    }
    for campo, atual in comparacoes.items():
        veio = _celula(linha.get(campo))
        if campo == "unidade_medida" and not veio:
            continue
        if campo == "forma_calculo" and not veio:
            continue
        if veio and veio != atual:
            erros.append(
                f"Linha {numero}: o indicador {codigo} já foi descrito nesta importação "
                f"com outro valor em {campo}."
            )


def _linha_tem_regra(linha):
    return any(_celula(linha.get(campo)) for campo in _CAMPOS_DE_REGRA)


def _ler_csv(texto):
    primeira = texto.splitlines()[0]
    delimitador = ";" if ";" in primeira else ","
    leitor = csv.DictReader(StringIO(texto), delimiter=delimitador)
    if not leitor.fieldnames:
        raise ValidationError({"arquivo": "O arquivo não tem cabeçalho."})
    nomes = [_normalizar_coluna(nome) for nome in leitor.fieldnames]
    if "codigo" not in nomes or "nome" not in nomes:
        raise ValidationError({"arquivo": "O cabeçalho precisa das colunas codigo e nome."})
    linhas = []
    for indice, bruta in enumerate(leitor, start=2):
        if bruta is None or not any((valor or "").strip() for valor in bruta.values() if valor):
            continue
        linha = {}
        for original, valor in bruta.items():
            if original is None:
                continue
            linha[_normalizar_coluna(original)] = valor
        linhas.append((indice, linha))
    if not linhas:
        raise ValidationError({"arquivo": "O arquivo não tem indicadores."})
    return linhas


def _normalizar_coluna(nome):
    texto = unicodedata.normalize("NFKD", nome or "")
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = texto.strip().lower().replace(" ", "_").replace("-", "_")
    return _ALIAS_COLUNA.get(texto, texto)


def _montar_indicador(dados, conhecidos=None):
    normativa = _normativa_por_id(dados.get("normativa") or dados.get("normativa_id"))
    codigo = _texto(dados.get("codigo"), "codigo")
    if Indicador.objects.filter(normativa=normativa, codigo=codigo).exists():
        raise ValidationError({"codigo": "Já existe indicador com este código nesta normativa."})
    nivel = _escolha(dados.get("nivel") or NivelIndicador.INDICADOR, NivelIndicador.values, "nivel")
    indicador = Indicador(
        normativa=normativa,
        codigo=codigo,
        nome=_texto(dados.get("nome"), "nome"),
        nivel=nivel,
        unidade_medida=_texto(dados.get("unidade_medida"), obrigatorio=False) or "%",
        forma_calculo=_escolha(
            dados.get("forma_calculo") or FormaCalculo.PROPORCAO,
            FormaCalculo.values,
            "forma_calculo",
        ),
        formula=_texto(dados.get("formula"), obrigatorio=False),
        ativo=_booleano(dados.get("ativo", True)),
        pai=_resolver_pai(normativa, _texto(dados.get("codigo_pai") or dados.get("pai"), obrigatorio=False), nivel, conhecidos),
    )
    return indicador


def _resolver_pai(normativa, codigo_pai, nivel, conhecidos=None):
    if nivel == NivelIndicador.INDICADOR:
        if codigo_pai:
            raise ValidationError({"pai": "Indicador de primeiro nível não tem pai."})
        return None
    if not codigo_pai:
        raise ValidationError({"pai": "Informe o indicador pai."})
    pai = None
    if conhecidos is not None:
        pai = conhecidos.get(codigo_pai)
    if pai is None:
        pai = Indicador.objects.filter(normativa=normativa, codigo=codigo_pai).first()
    if pai is None:
        raise ValidationError({"pai": f"O indicador pai '{codigo_pai}' não existe nesta normativa."})
    return pai


def _pai_informado(normativa, dados, nivel):
    if "codigo_pai" in dados:
        codigo = _texto(dados.get("codigo_pai"), obrigatorio=False)
    elif dados.get("pai") in ("", None):
        codigo = ""
    else:
        pai = Indicador.objects.filter(pk=dados.get("pai"), normativa=normativa).first()
        if pai is None and dados.get("pai") not in ("", None):
            raise ValidationError({"pai": "Indicador pai não encontrado nesta normativa."})
        return pai if nivel != NivelIndicador.INDICADOR else None
    return _resolver_pai(normativa, codigo, nivel)


def _indicador_por_referencia(dados):
    if dados.get("indicador"):
        indicador = Indicador.objects.filter(pk=dados.get("indicador")).first()
        if indicador is None:
            raise ValidationError({"indicador": "Indicador não encontrado."})
        return indicador
    normativa = _normativa_por_id(dados.get("normativa") or dados.get("normativa_id"))
    codigo = _texto(dados.get("codigo"), "codigo")
    indicador = Indicador.objects.filter(normativa=normativa, codigo=codigo).first()
    if indicador is None:
        raise ValidationError({"codigo": "Indicador não encontrado nesta normativa."})
    return indicador


def _preencher_regra(regra, dados):
    if "abrangencia" in dados:
        regra.abrangencia = _texto(dados.get("abrangencia"), obrigatorio=False)
    regra.peso_portaria = _decimal(dados.get("peso_portaria"), "peso_portaria", obrigatorio=True)
    if "peso_excepcional" in dados:
        regra.peso_excepcional = _decimal(dados.get("peso_excepcional"), "peso_excepcional", obrigatorio=False)
    if "meta" in dados:
        regra.meta = _decimal(dados.get("meta"), "meta", obrigatorio=False)


def _normativa_por_id(valor):
    if valor in ("", None):
        raise ValidationError({"normativa": "Informe a normativa."})
    normativa = Normativa.objects.filter(pk=valor).first()
    if normativa is None:
        raise ValidationError({"normativa": "Normativa não encontrada."})
    return normativa


def _salvar(objeto):
    objeto.full_clean()
    objeto.save()


def _exige(usuario, permissao):
    if not usuario_tem_permissao(usuario, permissao):
        raise PermissionDenied


def _auditar(usuario, operacao, entidade, identificador, anterior, novo):
    registrar(
        usuario=usuario,
        operacao=operacao,
        entidade=entidade,
        identificador=identificador,
        valor_anterior=_json(anterior),
        valor_novo=_json(novo),
    )


def _json(valor):
    if valor in ("", None):
        return ""
    if isinstance(valor, str):
        return valor
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, default=str)


def _foto_normativa(obj):
    return {
        "codigo": obj.codigo,
        "nome": obj.nome,
        "referencia_portaria": obj.referencia_portaria,
        "vigencia_inicio": obj.vigencia_inicio.isoformat(),
        "vigencia_fim": obj.vigencia_fim.isoformat() if obj.vigencia_fim else None,
        "situacao": obj.situacao,
    }


def _foto_competencia(obj):
    return {"ano": obj.ano, "mes": obj.mes, "normativa": obj.normativa.codigo}


def _foto_indicador(obj):
    return {
        "codigo": obj.codigo,
        "nome": obj.nome,
        "nivel": obj.nivel,
        "pai": obj.pai.codigo if obj.pai_id else None,
        "unidade_medida": obj.unidade_medida,
        "forma_calculo": obj.forma_calculo,
        "formula": obj.formula,
        "ativo": obj.ativo,
        "normativa": obj.normativa.codigo,
    }


def _foto_regra(obj):
    return {
        "indicador": obj.indicador.codigo,
        "normativa": obj.indicador.normativa.codigo,
        "cargo": obj.cargo,
        "tipo_unidade": obj.tipo_unidade,
        "abrangencia": obj.abrangencia,
        "peso_portaria": str(obj.peso_portaria),
        "peso_excepcional": None if obj.peso_excepcional is None else str(obj.peso_excepcional),
        "meta": None if obj.meta is None else str(obj.meta),
        "peso_vigente": str(obj.peso_vigente),
    }


def _id_indicador(obj):
    return f"{obj.normativa.codigo}/{obj.codigo}"


def _id_regra(obj):
    return f"{_id_indicador(obj.indicador)}/{obj.cargo or '-'}/{obj.tipo_unidade or '-'}"


def _mapa(dados):
    if hasattr(dados, "dict"):
        return dados.dict()
    return dict(dados)


def _celula(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def _texto(valor, campo="valor", obrigatorio=True):
    texto = _celula(valor)
    if not texto and obrigatorio:
        raise ValidationError({campo: "Preencha este campo."})
    return texto


def _inteiro(valor, campo):
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        raise ValidationError({campo: "Informe um número inteiro."}) from None


def _data(valor, campo, obrigatorio=True):
    if valor in ("", None):
        if obrigatorio:
            raise ValidationError({campo: "Informe a data no formato AAAA-MM-DD."})
        return None
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor).strip()[:10])
    except ValueError:
        raise ValidationError({campo: "Informe a data no formato AAAA-MM-DD."}) from None


def _decimal(valor, campo, obrigatorio):
    if valor in ("", None):
        if obrigatorio:
            raise ValidationError({campo: "Informe um número."})
        return None
    if isinstance(valor, Decimal):
        numero = valor
    else:
        texto = str(valor).strip().replace("%", "").replace(",", ".")
        try:
            numero = Decimal(texto)
        except InvalidOperation:
            raise ValidationError({campo: "Informe um número."}) from None
    return numero.quantize(Decimal("0.01"))


def _escolha(valor, opcoes, campo):
    texto = _celula(valor)
    if texto not in opcoes:
        raise ValidationError({campo: f"Use um destes valores: {', '.join(opcoes)}."})
    return texto


def _booleano(valor):
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in {"1", "true", "sim", "s", "ativo"}
