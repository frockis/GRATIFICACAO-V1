import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from cadastro.services import Autor, ImportacaoInvalida, importar

ARQUIVO_PROTOTIPO = Path(__file__).resolve().parents[2] / "dados_prototipo.json"


class Command(BaseCommand):
    help = (
        "Importa distritos, unidades e usuários de um JSON (tudo ou nada). "
        "Sem argumento, carrega os mesmos dados fictícios do src/data/mockData.ts."
    )

    def add_arguments(self, parser):
        parser.add_argument("arquivo", nargs="?", type=Path, default=ARQUIVO_PROTOTIPO)

    def handle(self, arquivo: Path, **opts):
        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise CommandError(f"Não consegui ler {arquivo}: {e}")

        try:
            resumo = importar(dados, Autor(nome="Carga inicial"))
        except ImportacaoInvalida as e:
            for erro in e.erros:
                self.stderr.write(f"[{erro['secao']}][{erro['indice']}] {erro['erros']}")
            raise CommandError(str(e))

        for secao, total in resumo.items():
            self.stdout.write(f"{secao}: {total}")
        self.stdout.write(self.style.SUCCESS("Importação concluída."))
