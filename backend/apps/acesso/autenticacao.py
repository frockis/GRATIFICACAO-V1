"""Autenticação provisória do protótipo (modo demonstração).

O front ainda não tem login: o seletor de perfil do Header manda o perfil no
cabeçalho X-Perfil e o nome da pessoa em X-Usuario (URL-encoded). Com
DEBUG=1 e SGGD_PERFIL_SIMULADO=1, esta classe troca o perfil pelo usuário de
demonstração "demo-<perfil>", que pertence ao papel (Group) equivalente. Assim
as permissões continuam sendo verificadas pelo Controle de Acesso
(ExigePermissao), e não pelo front.

Fora desse modo a classe não faz nada (retorna None) e vale só a sessão do
Django. Deve sair quando a autenticação institucional (OIDC/SAML) for definida.
"""

from dataclasses import dataclass
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth.models import Group
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from .models import Usuario

# Perfil do seletor do front (frontend/src/types/index.ts → PerfilId) → papel do Controle de Acesso.
PAPEL_DO_PERFIL = {
    "configurador": "Configurador",
    "seab": "CAM/SECOGE",
    "gestor": "Avaliado",
    "coordenador": "Avaliado",
}


@dataclass(frozen=True)
class IdentidadeSimulada:
    """Fica em request.auth: quem o front diz que está operando (para a auditoria)."""

    perfil: str
    nome: str


def modo_simulado_ativo():
    return bool(settings.DEBUG and getattr(settings, "SGGD_PERFIL_SIMULADO", False))


def _usuario_demo(perfil, papel):
    usuario, criado = Usuario.objects.get_or_create(
        username=f"demo-{perfil}",
        defaults={"first_name": "Demonstração", "last_name": perfil},
    )
    if criado:
        usuario.set_unusable_password()
        usuario.save(update_fields=["password"])
        try:
            usuario.groups.add(Group.objects.get(name=papel))
        except Group.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                f"Papel {papel} não encontrado. Rode as migrações (python manage.py migrate)."
            ) from None
    return usuario


class PerfilSimuladoAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if not modo_simulado_ativo():
            return None
        perfil = request.headers.get("X-Perfil", "").strip()
        if not perfil:
            return None
        papel = PAPEL_DO_PERFIL.get(perfil)
        if papel is None:
            raise exceptions.AuthenticationFailed(f"Perfil simulado desconhecido: {perfil}.")

        usuario = _usuario_demo(perfil, papel)
        if not usuario.is_active:
            raise exceptions.AuthenticationFailed("Usuário de demonstração inativo.")
        nome = unquote(request.headers.get("X-Usuario", "")).strip() or usuario.get_username()
        return usuario, IdentidadeSimulada(perfil=perfil, nome=nome)
