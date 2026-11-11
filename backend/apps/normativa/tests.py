from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.auditoria.interface import consultar

from . import services
from .interface import (
    CompetenciaNaoCadastrada,
    indicadores_para_coleta,
    regras_para_apuracao,
    soma_pesos_de_primeiro_nivel,
)
from .models import Indicador, RegraCalculo

EXEMPLO = Path(__file__).resolve().parent / "exemplo_indicadores.csv"
SENHA = "Senha-de-teste-123"


def _pessoa(username, papel=None):
    usuario = get_user_model().objects.create_user(username, password=SENHA)
    if papel:
        usuario.groups.add(Group.objects.get(name=papel))
    return usuario


class CadastroTests(TestCase):
    def setUp(self):
        self.configurador = _pessoa("diana", "Configurador")
        self.tecnico = _pessoa("ana", "Técnico")

    def _normativa(self):
        return services.cadastrar_normativa(
            self.configurador,
            {
                "codigo": "CAM-1.2",
                "nome": "Critérios de avaliação e monitoramento 1.2",
                "referencia_portaria": "Portaria da gratificação por desempenho",
                "vigencia_inicio": "2025-01-01",
                "vigencia_fim": "2025-12-31",
            },
        )

    def test_tecnico_nao_cadastra_normativa(self):
        with self.assertRaises(PermissionDenied):
            services.cadastrar_normativa(
                self.tecnico,
                {
                    "codigo": "CAM-1.2",
                    "nome": "Critérios",
                    "vigencia_inicio": "2025-01-01",
                },
            )

    def test_cadastro_de_normativa_competencia_e_indicador_vai_para_auditoria(self):
        normativa = self._normativa()
        services.cadastrar_competencia(
            self.configurador,
            {"normativa": normativa.id, "ano": 2025, "mes": 2},
        )
        indicador = services.cadastrar_indicador(
            self.configurador,
            {
                "normativa": normativa.id,
                "codigo": "1",
                "nome": "Materiais no Hórus",
                "formula": "Encerradas no prazo / total",
            },
        )
        regra = services.configurar_regra(
            self.configurador,
            {
                "indicador": indicador.id,
                "cargo": "coordenador_us",
                "tipo_unidade": "USF",
                "peso_portaria": "20",
                "peso_excepcional": "0",
                "meta": "100",
            },
        )

        self.assertEqual(regra.peso_portaria, Decimal("20.00"))
        self.assertEqual(regra.peso_vigente, Decimal("0.00"))
        entidades = {registro.entidade for registro in consultar()}
        self.assertEqual(entidades, {"normativa", "competencia", "indicador", "regra_calculo"})
        rastro = consultar(entidade="indicador", identificador="CAM-1.2/1")
        self.assertEqual(rastro[0].usuario_identificacao, "diana")
        self.assertEqual(rastro[0].operacao, "cadastrar_indicador")

    def test_competencia_fora_da_vigencia_e_recusada(self):
        normativa = self._normativa()

        with self.assertRaises(ValidationError) as bloco:
            services.cadastrar_competencia(
                self.configurador,
                {"normativa": normativa.id, "ano": 2024, "mes": 12},
            )

        self.assertIn("vigência", str(bloco.exception))

    def test_peso_acima_de_100_e_recusado(self):
        normativa = self._normativa()
        indicador = services.cadastrar_indicador(
            self.configurador,
            {"normativa": normativa.id, "codigo": "1", "nome": "Hórus"},
        )

        with self.assertRaises(ValidationError):
            services.configurar_regra(
                self.configurador,
                {"indicador": indicador.id, "peso_portaria": "150"},
            )

    def test_importacao_com_pai_inexistente_nao_grava_nada(self):
        normativa = self._normativa()
        conteudo = "codigo;nome;nivel;codigo_pai\n2.2;Abono;subindicador;9\n"

        with self.assertRaises(ValidationError) as bloco:
            services.importar_indicadores(self.configurador, normativa.id, conteudo)

        self.assertIn("9", str(bloco.exception))
        self.assertEqual(Indicador.objects.count(), 0)
        self.assertEqual(consultar(entidade="indicador"), [])

    def test_arquivo_de_exemplo_monta_regras_para_apuracao_e_coleta(self):
        normativa = self._normativa()
        services.cadastrar_competencia(
            self.configurador,
            {"normativa": normativa.id, "ano": 2025, "mes": 2},
        )
        services.importar_indicadores(self.configurador, normativa.id, EXEMPLO.read_text(encoding="utf-8"))

        regras = regras_para_apuracao(ano=2025, mes=2, cargo="coordenador_us", tipo_unidade="USF")
        self.assertEqual(soma_pesos_de_primeiro_nivel(regras), Decimal("100"))
        gestao = next(regra for regra in regras if regra.indicador_codigo == "2")
        self.assertEqual(gestao.forma_calculo, "media_subindicadores")
        self.assertIn("peso vigente", gestao.orientacao_calculo)

        snb2 = regras_para_apuracao(ano=2025, mes=2, cargo="SnB2")
        gestao_snb2 = next(regra for regra in snb2 if regra.indicador_codigo == "2")
        self.assertEqual(gestao_snb2.peso_portaria, Decimal("20.00"))
        self.assertEqual(gestao_snb2.peso_vigente, Decimal("15.00"))

        coleta = indicadores_para_coleta(ano=2025, mes=2, cargo="coordenador_us", tipo_unidade="USF")
        codigos = [item.codigo for item in coleta]
        self.assertEqual(codigos, ["1", "2", "2.2", "3", "4"])
        abono = next(item for item in coleta if item.codigo == "2.2")
        self.assertEqual(abono.pai_codigo, "2")
        self.assertIsNone(abono.meta)

        with self.assertRaises(CompetenciaNaoCadastrada):
            regras_para_apuracao(ano=2025, mes=3)


class ApiTests(TestCase):
    def setUp(self):
        self.configurador = _pessoa("diana", "Configurador")
        self.tecnico = _pessoa("ana", "Técnico")
        self.cliente = APIClient()

    def _preparar_exemplo(self):
        self.cliente.force_authenticate(user=self.configurador)
        normativa = self.cliente.post(
            "/api/normativa/normativas/",
            {
                "codigo": "CAM-1.2",
                "nome": "Critérios de avaliação e monitoramento 1.2",
                "vigencia_inicio": "2025-01-01",
                "vigencia_fim": "2025-12-31",
            },
            format="json",
        )
        self.assertEqual(normativa.status_code, 201, normativa.data)
        competencia = self.cliente.post(
            "/api/normativa/competencias/",
            {"normativa": normativa.data["id"], "ano": 2025, "mes": 2},
            format="json",
        )
        self.assertEqual(competencia.status_code, 201, competencia.data)
        arquivo = SimpleUploadedFile(
            "indicadores.csv",
            EXEMPLO.read_bytes(),
            content_type="text/csv",
        )
        importacao = self.cliente.post(
            "/api/normativa/indicadores/importar/",
            {"arquivo": arquivo, "normativa": normativa.data["id"]},
            format="multipart",
        )
        self.assertEqual(importacao.status_code, 201, importacao.data)
        self.assertEqual(importacao.data["quantidade"], 6)
        self.assertEqual(RegraCalculo.objects.count(), 6)
        return normativa.data["id"]

    def test_tecnico_nao_cadastra_pela_api_mas_le_o_que_a_coleta_precisa(self):
        self._preparar_exemplo()
        self.cliente.force_authenticate(user=self.tecnico)

        bloqueio = self.cliente.post(
            "/api/normativa/indicadores/",
            {"normativa": 1, "codigo": "9", "nome": "Fora do papel"},
            format="json",
        )
        self.assertEqual(bloqueio.status_code, 403)

        leitura = self.cliente.get(
            "/api/normativa/coleta/indicadores/",
            {"ano": 2025, "mes": 2, "cargo": "coordenador_us", "tipo_unidade": "USF"},
        )
        self.assertEqual(leitura.status_code, 200)
        codigos = [item["codigo"] for item in leitura.data]
        self.assertIn("2.2", codigos)
        self.assertNotIn("5", codigos)

        apuracao = self.cliente.get(
            "/api/normativa/apuracao/regras/",
            {"ano": 2025, "mes": 2, "cargo": "gg"},
        )
        self.assertEqual(apuracao.status_code, 200)
        self.assertEqual([item["indicador_codigo"] for item in apuracao.data], ["5"])
        self.assertEqual(apuracao.data[0]["peso_vigente"], "100.00")

    def test_sem_login_a_leitura_e_recusada(self):
        resposta = self.cliente.get("/api/normativa/coleta/indicadores/", {"ano": 2025, "mes": 2})

        self.assertEqual(resposta.status_code, 403)

    def test_competencia_desconhecida_responde_404(self):
        self.cliente.force_authenticate(user=self.tecnico)

        resposta = self.cliente.get("/api/normativa/apuracao/regras/", {"ano": 2025, "mes": 8})

        self.assertEqual(resposta.status_code, 404)
