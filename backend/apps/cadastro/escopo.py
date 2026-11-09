"""Escopo de visualização: o que cada usuário pode ver do cadastro e dos resultados.

Item do plano de desenvolvimento: "Controla quais resultados são disponibilizados
para usuário visualizar". É a mesma regra do front (frontend/src/utils/escopo.ts),
agora aplicada no servidor:

- quem gerencia o cadastro (acesso.cadastrar_unidade ou acesso.cadastrar_avaliado): município;
- pessoa ativa com perfil SEAB/CAM ou Configurador: município;
- Gestor de Unidade: a própria unidade (e o distrito dela);
- Coordenador Distrital: o próprio distrito;
- sem pessoa ativa ligada ao login: nada (nunca o município por engano).

A pessoa é o Avaliado ligado ao login (Avaliado.usuario). No modo demonstração do
Controle de Acesso o login é "demo-<perfil>"; aí a pessoa é a mesma que o front usa,
o primeiro Avaliado ativo daquele perfil (usuarioDoPerfil em escopo.ts).

Outros componentes filtram os seus dados por unidade com:

    from apps.cadastro.interface import escopo_do_request
    resultados.filter(unidade_id__in=escopo_do_request(request).unidade_ids())
"""
from dataclasses import dataclass

from apps.acesso.interface import IdentidadeSimulada, usuario_tem_permissao

from .models import Avaliado, Distrito, PerfilId, Status, Unidade

# Quem administra o cadastro precisa enxergar o município inteiro.
PERMISSOES_DE_GESTAO = ("acesso.cadastrar_unidade", "acesso.cadastrar_avaliado")
PERFIS_MUNICIPAIS = {PerfilId.SEAB.value, PerfilId.CONFIGURADOR.value}


@dataclass(frozen=True)
class Escopo:
    """Recorte territorial. Sem nenhum campo preenchido, o escopo é vazio (não vê nada)."""

    municipal: bool = False
    distrito_id: str | None = None
    unidade_id: str | None = None

    @property
    def vazio(self) -> bool:
        return not (self.municipal or self.distrito_id or self.unidade_id)

    def unidades(self):
        qs = Unidade.objects.all()
        if self.municipal:
            return qs
        if self.unidade_id:
            return qs.filter(pk=self.unidade_id)
        if self.distrito_id:
            return qs.filter(distrito_id=self.distrito_id)
        return qs.none()

    def distritos(self):
        qs = Distrito.objects.all()
        if self.municipal:
            return qs
        if self.distrito_id:
            return qs.filter(pk=self.distrito_id)
        return qs.none()

    def avaliados(self):
        qs = Avaliado.objects.all()
        if self.municipal:
            return qs
        if self.unidade_id:
            return qs.filter(unidade_id=self.unidade_id)
        if self.distrito_id:
            return qs.filter(distrito_id=self.distrito_id)
        return qs.none()

    def unidade_ids(self) -> list[str]:
        """Ids das unidades visíveis, para outros componentes filtrarem resultados."""
        return list(self.unidades().values_list("pk", flat=True))

    def alcanca_unidade(self, unidade_id: str) -> bool:
        return self.unidades().filter(pk=unidade_id).exists()


def pessoa_do_request(request) -> Avaliado | None:
    """Avaliado ativo de quem fez a requisição (ou None)."""
    autenticacao = getattr(request, "auth", None)
    if isinstance(autenticacao, IdentidadeSimulada):
        return Avaliado.objects.filter(perfil=autenticacao.perfil, status=Status.ATIVO).order_by("pk").first()
    usuario = getattr(request, "user", None)
    if not (usuario and usuario.is_authenticated):
        return None
    return Avaliado.objects.filter(usuario=usuario, status=Status.ATIVO).first()


def escopo_do_request(request) -> Escopo:
    """Escopo de quem fez a requisição (request do Django ou do DRF)."""
    usuario = getattr(request, "user", None)
    if not (usuario and usuario.is_authenticated):
        return Escopo()
    if any(usuario_tem_permissao(usuario, p) for p in PERMISSOES_DE_GESTAO):
        return Escopo(municipal=True)

    pessoa = pessoa_do_request(request)
    if pessoa is None:
        return Escopo()
    if pessoa.perfil in PERFIS_MUNICIPAIS:
        return Escopo(municipal=True)
    if pessoa.perfil == PerfilId.GESTOR:
        # Gestor sem unidade não passa no Avaliado.clean; se acontecer, não vê nada.
        return Escopo(unidade_id=pessoa.unidade_id, distrito_id=pessoa.distrito_id) if pessoa.unidade_id else Escopo()
    if pessoa.perfil == PerfilId.COORDENADOR:
        return Escopo(distrito_id=pessoa.distrito_id)
    return Escopo()
