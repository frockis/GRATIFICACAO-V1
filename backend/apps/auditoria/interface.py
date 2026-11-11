"""Contrato do registro de auditoria.

Os outros componentes importam somente este módulo. A normativa chama
`registrar` ao gravar normativa, competência, indicador e regra de cálculo.
Quem for evoluir a tela de auditoria deve manter estas duas funções.
"""

from dataclasses import dataclass
from datetime import datetime

from .models import RegistroAuditoria


@dataclass(frozen=True)
class RegistroConsulta:
    id: int
    ocorrido_em: datetime
    usuario_id: int | None
    usuario_identificacao: str
    operacao: str
    entidade: str
    identificador: str
    valor_anterior: str
    valor_novo: str


def registrar(*, usuario, operacao, entidade, identificador, valor_anterior="", valor_novo=""):
    """Guarda um fato. O chamador já conferiu a permissão da operação dele.

    `operacao` é o nome do que aconteceu (ex.: cadastrar_indicador).
    `entidade` é o tipo do registro (ex.: indicador, normativa).
    `identificador` é a chave legível, não só o id numérico.
    `valor_anterior` e `valor_novo` são textos, em geral JSON.
    """
    if not usuario or not getattr(usuario, "is_authenticated", False):
        raise ValueError("O registro de auditoria precisa de um usuário autenticado.")

    return RegistroAuditoria.objects.create(
        usuario=usuario,
        usuario_identificacao=usuario.get_username(),
        operacao=operacao,
        entidade=entidade,
        identificador=identificador,
        valor_anterior=valor_anterior or "",
        valor_novo=valor_novo or "",
    )


def consultar(*, entidade="", identificador=""):
    """Devolve os registros já gravados, do mais antigo para o mais novo.

    Filtros vazios não restringem. Serve para a futura tela de auditoria e
    para os outros componentes conferirem o que enviaram.
    """
    consulta = RegistroAuditoria.objects.all()
    if entidade:
        consulta = consulta.filter(entidade=entidade)
    if identificador:
        consulta = consulta.filter(identificador=identificador)
    return [
        RegistroConsulta(
            id=registro.id,
            ocorrido_em=registro.ocorrido_em,
            usuario_id=registro.usuario_id,
            usuario_identificacao=registro.usuario_identificacao,
            operacao=registro.operacao,
            entidade=registro.entidade,
            identificador=registro.identificador,
            valor_anterior=registro.valor_anterior,
            valor_novo=registro.valor_novo,
        )
        for registro in consulta
    ]
