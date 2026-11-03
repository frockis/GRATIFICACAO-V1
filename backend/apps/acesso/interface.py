"""Interface pública do Controle de Acesso.

Os demais componentes importam somente este módulo (contrato do import-linter).

Cada operação protegida é uma Permission do Django do catálogo
apps.acesso.models.Operacao ("acesso.<codename>"). Papéis são Groups que
recebem essas permissões; por isso o código verifica permissões, nunca nomes
de papéis.

Uso em uma view do DRF:

    class EnviarParaFolha(APIView):
        permission_classes = [ExigePermissao]
        permissoes_exigidas = ("acesso.enviar_resultado_folha",)

Uso fora de views (ex.: services.py):

    if not usuario_tem_permissao(usuario, "acesso.enviar_resultado_folha"):
        raise PermissionDenied

Ter a permissão não basta para operações sobre dados de uma pessoa (ex.: o
Avaliado só consulta a própria pontuação): o componente dono também precisa
verificar o escopo, que ainda não está definido.
"""

from django.core.exceptions import ImproperlyConfigured
from rest_framework.permissions import BasePermission


def usuario_tem_permissao(usuario, permissao):
    """Diz se o usuário pode executar a operação "app_label.codename".

    Usuários anônimos ou inativos nunca têm permissão. Superusuários têm todas.
    """
    return bool(usuario and usuario.is_authenticated and usuario.has_perm(permissao))


class ExigePermissao(BasePermission):
    """Permite a requisição só se o usuário tiver todas as `permissoes_exigidas` da view.

    Sem usuário autenticado, o DRF responde "não autenticado"; autenticado sem a
    permissão, responde 403.
    """

    message = "Você não tem permissão para executar esta operação."

    def has_permission(self, request, view):
        permissoes = getattr(view, "permissoes_exigidas", None)
        if not permissoes:
            raise ImproperlyConfigured(
                f"{type(view).__name__} usa ExigePermissao, mas não define permissoes_exigidas."
            )
        return all(usuario_tem_permissao(request.user, p) for p in permissoes)
