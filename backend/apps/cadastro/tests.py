import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from auditoria.models import RegistroAuditoria

from . import services
from .models import Avaliado, Distrito, Unidade

DADOS = json.loads((Path(__file__).parent / "dados_prototipo.json").read_text(encoding="utf-8"))
SEAB = {"HTTP_X_PERFIL": "seab", "HTTP_X_USUARIO": "Patr%C3%ADcia%20Gomes%20Freitas"}
GESTOR = {"HTTP_X_PERFIL": "gestor", "HTTP_X_USUARIO": "Ana"}


class ModeloTest(TestCase):
    def setUp(self):
        self.d1 = Distrito.objects.create(id="d1", nome="Distrito I")
        self.d2 = Distrito.objects.create(id="d2", nome="Distrito II")
        self.u1 = Unidade.objects.create(id="u1", nome="USF A", distrito=self.d1, tipo="USF")
        self.autor = services.Autor("Teste", "seab")

    def test_id_gerado_no_padrao_do_prototipo(self):
        u = services.salvar(Unidade(nome="USF B", distrito=self.d1, tipo="USF"), self.autor)
        self.assertEqual(u.id, "u2")
        a = services.salvar(Avaliado(nome="X", email="x@x.org", perfil="seab"), self.autor)
        self.assertEqual(a.id, "us1")

    def test_gestor_exige_unidade_e_herda_distrito(self):
        with self.assertRaises(ValidationError) as ctx:
            services.salvar(Avaliado(nome="G", email="g@x.org", perfil="gestor"), self.autor)
        self.assertIn("unidade", ctx.exception.message_dict)
        a = services.salvar(Avaliado(nome="G", email="g@x.org", perfil="gestor", unidade=self.u1), self.autor)
        self.assertEqual(a.distrito_id, "d1")
        self.assertEqual(a.tipo_unidade, "USF")

    def test_gestor_com_distrito_divergente(self):
        with self.assertRaises(ValidationError):
            services.salvar(
                Avaliado(nome="G", email="g@x.org", perfil="gestor", unidade=self.u1, distrito=self.d2), self.autor
            )

    def test_coordenador_sem_unidade_com_distrito(self):
        with self.assertRaises(ValidationError):
            services.salvar(Avaliado(nome="C", email="c@x.org", perfil="coordenador", unidade=self.u1), self.autor)
        with self.assertRaises(ValidationError):
            services.salvar(Avaliado(nome="C", email="c@x.org", perfil="coordenador"), self.autor)
        services.salvar(Avaliado(nome="C", email="c@x.org", perfil="coordenador", distrito=self.d1), self.autor)

    def test_seab_sem_vinculo_territorial(self):
        with self.assertRaises(ValidationError):
            services.salvar(Avaliado(nome="S", email="s@x.org", perfil="seab", distrito=self.d1), self.autor)

    def test_unidade_id_inexistente_vira_erro_e_nao_500(self):
        a = Avaliado(nome="G", email="g@x.org", perfil="gestor")
        a.unidade_id = "u999"
        with self.assertRaises(ValidationError):
            services.salvar(a, self.autor)

    def test_inativar_unidade_com_gente_ativa_bloqueia(self):
        services.salvar(Avaliado(nome="G", email="g@x.org", perfil="gestor", unidade=self.u1), self.autor)
        with self.assertRaises(ValidationError):
            services.inativar_unidade(self.u1, self.autor)

    def test_nao_troca_distrito_de_unidade_com_pessoas(self):
        services.salvar(Avaliado(nome="G", email="G@X.org", perfil="gestor", unidade=self.u1), self.autor)
        self.assertTrue(Avaliado.objects.filter(email="g@x.org").exists())  # e-mail normalizado
        self.u1.distrito = self.d2
        with self.assertRaises(ValidationError) as ctx:
            services.salvar(self.u1, self.autor)
        self.assertIn("distrito", ctx.exception.message_dict)

    def test_auditoria_de_vinculo(self):
        u2 = services.salvar(Unidade(nome="USF B", distrito=self.d2, tipo="USF"), self.autor)
        a = services.salvar(Avaliado(nome="G", email="g@x.org", perfil="gestor", unidade=self.u1), self.autor)
        a.unidade = u2
        a.distrito = None
        services.salvar(a, self.autor)
        reg = RegistroAuditoria.objects.filter(operacao="Vínculo alterado").get()
        self.assertIn("unidade: USF A", reg.valor_anterior)
        self.assertIn("unidade: USF B", reg.novo_valor)
        self.assertEqual(reg.componente, "cadastro")
        self.assertEqual(reg.perfil, "SEAB/CAM — Monitoramento")

    def test_salvar_sem_mudanca_nao_gera_registro(self):
        antes = RegistroAuditoria.objects.count()
        services.salvar(self.u1, self.autor)  # u1 foi criado sem service: conta como alteração vazia
        self.assertEqual(RegistroAuditoria.objects.count(), antes)


class ImportacaoTest(TestCase):
    def test_carga_do_prototipo_e_idempotente(self):
        call_command("importar_cadastro", verbosity=0)
        self.assertEqual(Distrito.objects.count(), 3)
        self.assertEqual(Unidade.objects.count(), 4)
        self.assertEqual(Avaliado.objects.count(), 9)
        self.assertEqual(Avaliado.objects.get(id="us1").distrito_id, "d1")
        registros = RegistroAuditoria.objects.count()
        call_command("importar_cadastro", verbosity=0)
        self.assertEqual(Avaliado.objects.count(), 9)
        self.assertEqual(RegistroAuditoria.objects.count(), registros)  # nada mudou, nada auditado

    def test_tudo_ou_nada(self):
        ruim = {
            "distritos": [{"id": "d1", "nome": "Distrito I"}],
            "unidades": [
                {"id": "u1", "nome": "USF A", "distritoId": "d1", "tipo": "USF"},
                {"id": "u2", "nome": "Sem tipo", "distritoId": "d1"},
                {"id": "u3", "nome": "Distrito errado", "distritoId": "d9", "tipo": "USF"},
            ],
        }
        with self.assertRaises(services.ImportacaoInvalida) as ctx:
            services.importar(ruim, services.Autor())
        self.assertEqual([(e["secao"], e["indice"]) for e in ctx.exception.erros], [("unidades", 1), ("unidades", 2)])
        self.assertFalse(Distrito.objects.exists())
        self.assertFalse(RegistroAuditoria.objects.exists())


@override_settings(SGGD_PERFIL_SIMULADO=True)
class ApiTest(APITestCase):
    def setUp(self):
        services.importar(DADOS, services.Autor())

    def test_formato_igual_ao_front(self):
        r = self.client.get("/api/usuarios/", {"perfilId": "gestor"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 4)
        self.assertEqual(
            set(r.data[0].keys()),
            {"id", "nome", "email", "matricula", "perfilId", "unidadeId", "distritoId", "tipoUnidade", "status"},
        )
        self.assertEqual(r.data[0]["tipoUnidade"], "USF")
        u = self.client.get("/api/unidades/u1/").data
        self.assertEqual(u["distritoId"], "d1")
        self.assertEqual(len(self.client.get("/api/distritos/").data), 3)

    def test_gestor_nao_cadastra(self):
        r = self.client.post("/api/unidades/", {"nome": "USF Nova", "distritoId": "d1", "tipo": "USF"}, format="json", **GESTOR)
        self.assertEqual(r.status_code, 403)
        r = self.client.post("/api/unidades/", {"nome": "USF Nova", "distritoId": "d1", "tipo": "USF"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_seab_cadastra_altera_e_inativa(self):
        r = self.client.post("/api/unidades/", {"nome": "USF Nova", "distritoId": "d2", "tipo": "USF"}, format="json", **SEAB)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["id"], "u5")

        r = self.client.patch("/api/unidades/u5/", {"nome": "USF Nova II"}, format="json", **SEAB)
        self.assertEqual(r.status_code, 200, r.data)

        r = self.client.post("/api/unidades/u5/inativar/", **SEAB)
        self.assertEqual(r.data["status"], "Inativo")

        self.assertEqual(self.client.delete("/api/unidades/u5/", **SEAB).status_code, 405)

        reg = RegistroAuditoria.objects.filter(operacao="Unidade cadastrada").latest("id")
        self.assertEqual(reg.usuario, "Patrícia Gomes Freitas")

    def test_erros_com_nome_do_campo_do_front(self):
        r = self.client.post(
            "/api/usuarios/", {"nome": "Sem unidade", "email": "su@x.org", "perfilId": "gestor"}, format="json", **SEAB
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("unidadeId", r.data)

    def test_vinculos_para_apuracao(self):
        r = self.client.get("/api/vinculos/", {"distritoId": "d1"})
        # Ana (u1), Carlos (u2) e Marcela (coordenadora d1). SEAB/Configurador e inativos ficam fora.
        self.assertEqual([v["avaliadoId"] for v in r.data], ["us1", "us2", "us5"])
        r = self.client.get("/api/unidades/u3/vinculos/")
        self.assertEqual([v["nome"] for v in r.data], ["Fernanda Alves Rocha"])

    def test_importar_por_http(self):
        r = self.client.post(
            "/api/cadastro/importar/",
            {"unidades": [{"nome": "CAPS Centro", "distritoId": "d1", "tipo": "CAPS"}]},
            format="json",
            **SEAB,
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["unidades"], 1)

    def test_auditoria_no_formato_do_front(self):
        self.client.patch("/api/usuarios/us2/", {"unidadeId": "u3"}, format="json", **SEAB)
        r = self.client.get("/api/auditoria/", {"componente": "cadastro"})
        primeiro = r.data[0]
        self.assertEqual(primeiro["operacao"], "Vínculo alterado")
        self.assertEqual(
            set(primeiro.keys()),
            {"id", "usuario", "data", "horario", "operacao", "registroAfetado", "valorAnterior", "novoValor", "perfil", "localizacao", "componente"},
        )
