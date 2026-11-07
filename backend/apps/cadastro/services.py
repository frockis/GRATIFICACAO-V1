"""Regras do componente 'cadastro' e interface usada pelos outros componentes.

Toda escrita passa por aqui para (1) validar com as regras do modelo e
(2) enviar o registro para a auditoria, como pede o plano de desenvolvimento.
"""
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.forms.models import model_to_dict

from auditoria.services import registrar

from .models import Avaliado, Distrito, PerfilId, Status, Unidade

COMPONENTE = "cadastro"


@dataclass
class Autor:
    """Quem executou a operação (vem dos cabeçalhos do front ou do comando)."""

    nome: str = "Sistema"
    perfil: str = ""


# --------------------------------------------------------------------------- #
# Auditoria
# --------------------------------------------------------------------------- #

CAMPOS_AUDITADOS = {
    Unidade: ["nome", "distrito", "tipo", "cnes", "status"],
    Avaliado: ["nome", "email", "matricula", "perfil", "unidade", "distrito", "status"],
    Distrito: ["nome"],
}
CAMPOS_DE_VINCULO = {"perfil", "unidade", "distrito"}


def _foto(obj) -> dict:
    campos = CAMPOS_AUDITADOS[type(obj)]
    return {k: ("—" if v in (None, "") else str(v)) for k, v in model_to_dict(obj, fields=campos).items()}


def _nome_relacionado(campo: str, valor: str) -> str:
    if valor == "—":
        return valor
    if campo == "unidade":
        return Unidade.objects.filter(pk=valor).values_list("nome", flat=True).first() or valor
    if campo == "distrito":
        return Distrito.objects.filter(pk=valor).values_list("nome", flat=True).first() or valor
    if campo == "perfil":
        return PerfilId(valor).label if valor in PerfilId.values else valor
    return valor


def _descrever(foto: dict, campos) -> str:
    return "; ".join(f"{c}: {_nome_relacionado(c, foto[c])}" for c in campos) or "—"


def _localizacao(obj) -> str:
    if isinstance(obj, Unidade):
        return f"{obj.nome} — {obj.distrito.nome}"
    if isinstance(obj, Avaliado):
        if obj.unidade_id:
            return f"{obj.unidade.nome} — {obj.unidade.distrito.nome}"
        if obj.distrito_id:
            return obj.distrito.nome
    return "Município"


def _auditar(obj, autor: Autor, antes: dict | None):
    nome_classe = {Unidade: "Unidade", Avaliado: "Avaliado", Distrito: "Distrito"}[type(obj)]
    registro = f"{nome_classe} {obj.pk} · {obj}"
    depois = _foto(obj)
    comum = dict(componente=COMPONENTE, usuario=autor.nome, perfil=_perfil_label(autor.perfil))

    if antes is None:
        registrar(
            **comum,
            operacao=f"{nome_classe} cadastrado" if nome_classe != "Unidade" else "Unidade cadastrada",
            registro_afetado=registro,
            valor_anterior="—",
            novo_valor=_descrever(depois, depois.keys()),
            localizacao=_localizacao(obj),
        )
        return

    alterados = [c for c in depois if depois[c] != antes[c]]
    if not alterados:
        return

    if alterados == ["status"]:
        operacao = f"{nome_classe} {'reativad' if depois['status'] == Status.ATIVO else 'inativad'}"
        operacao += "a" if nome_classe == "Unidade" else "o"
    elif isinstance(obj, Avaliado) and CAMPOS_DE_VINCULO & set(alterados):
        operacao = "Vínculo alterado"
    else:
        operacao = f"{nome_classe} alterad{'a' if nome_classe == 'Unidade' else 'o'}"

    registrar(
        **comum,
        operacao=operacao,
        registro_afetado=registro,
        valor_anterior=_descrever(antes, alterados),
        novo_valor=_descrever(depois, alterados),
        localizacao=_localizacao(obj),
    )


def _perfil_label(perfil: str) -> str:
    return PerfilId(perfil).label if perfil in PerfilId.values else ""


# --------------------------------------------------------------------------- #
# Escrita
# --------------------------------------------------------------------------- #


@transaction.atomic
def salvar(obj, autor: Autor):
    """Valida, grava e audita uma Unidade, Avaliado ou Distrito (novo ou existente)."""
    antes = None
    if obj.pk and type(obj).objects.filter(pk=obj.pk).exists():
        antes = _foto(type(obj).objects.get(pk=obj.pk))
    obj.full_clean()
    obj.save()
    _auditar(obj, autor, antes)
    return obj


def inativar_unidade(unidade: Unidade, autor: Autor) -> Unidade:
    if unidade.avaliados.filter(status=Status.ATIVO).exists():
        raise ValidationError(
            {"status": "A unidade ainda tem pessoas ativas vinculadas. Mude o vínculo delas antes de inativar."}
        )
    unidade.status = Status.INATIVO
    return salvar(unidade, autor)


def inativar_avaliado(avaliado: Avaliado, autor: Autor) -> Avaliado:
    avaliado.status = Status.INATIVO
    return salvar(avaliado, autor)


def reativar(obj, autor: Autor):
    """Reativa Unidade ou Avaliado (Avaliado.clean impede vínculo com unidade inativa)."""
    obj.status = Status.ATIVO
    return salvar(obj, autor)


# --------------------------------------------------------------------------- #
# Leitura para outros componentes (Apuração e Homologação, Coleta, Recursos)
# --------------------------------------------------------------------------- #


def vinculos_unidade_pessoa(unidade_id: str | None = None, distrito_id: str | None = None):
    """Avaliados ativos com o seu vínculo (para 'apuração e homologação').

    Retorna só quem entra no cálculo: gestores de unidade e coordenadores distritais.
    """
    qs = (
        Avaliado.objects.filter(status=Status.ATIVO, perfil__in=[PerfilId.GESTOR, PerfilId.COORDENADOR])
        .select_related("unidade", "distrito")
        .order_by("id")
    )
    if unidade_id:
        qs = qs.filter(unidade_id=unidade_id)
    if distrito_id:
        qs = qs.filter(distrito_id=distrito_id)
    return [
        {
            "avaliadoId": a.id,
            "nome": a.nome,
            "perfilId": a.perfil,
            "unidadeId": a.unidade_id,
            "distritoId": a.distrito_id,
            "tipoUnidade": a.tipo_unidade,
        }
        for a in qs
    ]


# --------------------------------------------------------------------------- #
# Importação por JSON ("Cadastra avaliados e unidades por JSON/https")
# --------------------------------------------------------------------------- #


class ImportacaoInvalida(Exception):
    def __init__(self, erros: list[dict]):
        super().__init__("Importação rejeitada: nenhum registro foi gravado.")
        self.erros = erros


def _mensagens(e: ValidationError):
    return e.message_dict if hasattr(e, "error_dict") else e.messages


def _preencher(obj, item: dict, mapa: dict):
    """Copia campos do JSON (camelCase, como no front) para o modelo."""
    for chave_json, campo in mapa.items():
        if chave_json in item:
            setattr(obj, campo, item[chave_json] if item[chave_json] != "" else None)


MAPA_UNIDADE = {"nome": "nome", "distritoId": "distrito_id", "tipo": "tipo", "cnes": "cnes", "status": "status"}
MAPA_USUARIO = {
    "nome": "nome",
    "email": "email",
    "matricula": "matricula",
    "perfilId": "perfil",
    "unidadeId": "unidade_id",
    "distritoId": "distrito_id",
    "status": "status",
}


def preencher_unidade(obj: Unidade, item: dict, incluir_status: bool = True):
    mapa = MAPA_UNIDADE if incluir_status else {k: v for k, v in MAPA_UNIDADE.items() if k != "status"}
    _preencher(obj, item, mapa)


def preencher_usuario(obj: Avaliado, item: dict, incluir_status: bool = True):
    mapa = MAPA_USUARIO if incluir_status else {k: v for k, v in MAPA_USUARIO.items() if k != "status"}
    _preencher(obj, item, mapa)
    # Trocou de unidade sem dizer o distrito: o distrito passa a ser o da nova unidade (ver Avaliado.clean).
    if "unidadeId" in item and "distritoId" not in item:
        obj.distrito_id = None


def _importar_distrito(item, autor):
    obj = Distrito.objects.filter(pk=item.get("id")).first() if item.get("id") else None
    obj = obj or Distrito(id=item.get("id") or "")
    _preencher(obj, item, {"nome": "nome"})
    salvar(obj, autor)


def _importar_unidade(item, autor):
    obj = Unidade.objects.filter(pk=item.get("id")).first() if item.get("id") else None
    obj = obj or Unidade(id=item.get("id") or "")
    preencher_unidade(obj, item)
    salvar(obj, autor)


def _importar_avaliado(item, autor):
    obj = None
    if item.get("id"):
        obj = Avaliado.objects.filter(pk=item["id"]).first()
    elif item.get("email"):
        obj = Avaliado.objects.filter(email=item["email"]).first()
    obj = obj or Avaliado(id=item.get("id") or "")
    preencher_usuario(obj, item)
    salvar(obj, autor)


def importar(dados: dict, autor: Autor) -> dict:
    """Recebe {"distritos": [...], "unidades": [...], "usuarios": [...]} no formato do front.

    Cria ou atualiza pelo id. Tudo ou nada: com qualquer erro, nada é gravado.
    """
    if not isinstance(dados, dict):
        raise ImportacaoInvalida([{"secao": None, "indice": None, "erros": "Envie um objeto JSON."}])

    secoes = (("distritos", _importar_distrito), ("unidades", _importar_unidade), ("usuarios", _importar_avaliado))
    resumo = {secao: 0 for secao, _ in secoes}
    erros: list[dict] = []

    with transaction.atomic():
        for secao, importar_item in secoes:
            itens = dados.get(secao, [])
            if not isinstance(itens, list):
                erros.append({"secao": secao, "indice": None, "erros": "Deve ser uma lista."})
                continue
            for indice, item in enumerate(itens):
                try:
                    with transaction.atomic():
                        if not isinstance(item, dict):
                            raise ValidationError("Cada item deve ser um objeto.")
                        importar_item(item, autor)
                        resumo[secao] += 1
                except ValidationError as e:
                    erros.append({"secao": secao, "indice": indice, "erros": _mensagens(e)})
                except IntegrityError as e:
                    erros.append({"secao": secao, "indice": indice, "erros": str(e)})
        if erros:
            transaction.set_rollback(True)

    if erros:
        raise ImportacaoInvalida(erros)
    return resumo
