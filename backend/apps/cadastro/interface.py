"""Interface pública do Cadastro de Avaliados e Unidades.

Os demais componentes (apuração, coleta, recurso...) importam somente este módulo
(contrato do import-linter).
"""

from .services import vinculos_unidade_pessoa

__all__ = ["vinculos_unidade_pessoa"]
