"""Interface pública do Registro de Auditoria.

Os demais componentes importam somente este módulo (contrato do import-linter):

    from apps.auditoria.interface import registrar

    registrar(componente="cadastro", usuario=..., perfil=..., operacao=..., registro_afetado=...)
"""

from .models import RegistroAuditoria
from .services import registrar

__all__ = ["registrar", "registros"]


def registros(componente=None):
    """Registros de auditoria (mais recentes primeiro), opcionalmente de um componente."""
    qs = RegistroAuditoria.objects.all()
    if componente:
        qs = qs.filter(componente=componente)
    return qs
