"""Interface pública do Cadastro de Avaliados e Unidades.

Os demais componentes (apuração, coleta, recurso...) importam somente este módulo
(contrato do import-linter).

- vinculos_unidade_pessoa(): vínculo atual pessoa-unidade dos avaliados (apuração).
- escopo_do_request(request): o que quem fez a requisição pode ver. Ex.: a publicação
  mostra só os resultados de `escopo_do_request(request).unidade_ids()`.
"""

from .escopo import Escopo, escopo_do_request
from .services import vinculos_unidade_pessoa

__all__ = ["Escopo", "escopo_do_request", "vinculos_unidade_pessoa"]
