import json
from pathlib import Path
from unittest import mock

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APITestCase

from apps.auditoria.interface import registros

from . import models, services
from .interface import escopo_do_request
from .models import Avaliado, Distrito, Unidade

DADOS = json.loads((Path(__file__).parent / "dados_prototipo.json").read_text(encoding="utf-8"))


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
        reg = registros().filter(operacao="Vínculo alterado").get()
        self.assertIn("unidade: USF A", reg.valor_anterior)
        self.assertIn("unidade: USF B", reg.novo_valor)
        self.assertEqual(reg.componente, "cadastro")
        self.assertEqual(reg.perfil, "SEAB/CAM — Monitoramento")

    def test_salvar_sem_mudanca_nao_gera_registro(self):
        antes = registros().count()
        services.salvar(self.u1, self.autor)  # u1 foi criado sem service: conta como alteração vazia
        self.assertEqual(registros().count(), antes)

    def test_id_que_colide_nao_sobrescreve_outro_registro(self):
        # Simula dois cadastros simultâneos: o gerador devolve um id que outro acabou de gravar.
        with mock.patch("apps.cadastro.models.proximo_id", side_effect=["u1", "u2"]):
            nova = services.salvar(Unidade(nome="USF B", distrito=self.d2, tipo="UBT"), self.autor)
        self.assertEqual(nova.id, "u2")
        self.u1.refresh_from_db()
        self.assertEqual((self.u1.nome, self.u1.distrito_id, self.u1.tipo), ("USF A", "d1", "USF"))

    def test_colisao_em_outra_restricao_nao_repete(self):
        services.salvar(Avaliado(nome="X", email="x@x.org", perfil="seab"), self.autor)
        duplicado = Avaliado(nome="Y", email="x@x.org", perfil="seab")
        with mock.patch("apps.cadastro.models.proximo_id", wraps=models.proximo_id) as gerador:
            with self.assertRaises(IntegrityError), transaction.atomic():
                duplicado.save()  # sem full_clean: chega ao banco e bate no e-mail único
        self.assertEqual(gerador.call_count, 1)
        self.assertEqual(duplicado.id, "")

    def test_ligar_login_ao_avaliado_e_auditado(self):
        login = get_user_model().objects.create_user("gestor.a")
        a = services.salvar(Avaliado(nome="G", email="g@x.org", perfil="gestor", unidade=self.u1), self.autor)
        a.usuario = login
        services.salvar(a, self.autor)
        reg = registros().filter(operacao="Login vinculado").get()
        self.assertEqual((reg.valor_anterior, reg.novo_valor), ("usuario: —", "usuario: gestor.a"))
        a.usuario = None
        services.salvar(a, self.autor)
        self.assertTrue(registros().filter(operacao="Login desvinculado").exists())

    def test_login_so_pode_ser_de_uma_pessoa(self):
        login = get_user_model().objects.create_user("gestor.a")
        services.salvar(
            Avaliado(nome="G", email="g@x.org", perfil="gestor", unidade=self.u1, usuario=login), self.autor
        )
        with self.assertRaises(ValidationError) as ctx:
            services.salvar(Avaliado(nome="S", email="s@x.org", perfil="seab", usuario=login), self.autor)
        self.assertIn("usuario", ctx.exception.message_dict)


class ImportacaoTest(TestCase):
    def test_carga_do_prototipo_e_idempotente(self):
        call_command("importar_cadastro", verbosity=0)
        self.assertEqual(Distrito.objects.count(), 3)
        self.assertEqual(Unidade.objects.count(), 4)
        self.assertEqual(Avaliado.objects.count(), 9)
        self.assertEqual(Avaliado.objects.get(id="us1").distrito_id, "d1")
        total = registros().count()
        call_command("importar_cadastro", verbosity=0)
        self.assertEqual(Avaliado.objects.count(), 9)
        self.assertEqual(registros().count(), total)  # nada mudou, nada auditado

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
        self.assertFalse(registros().exists())


def _usuario(username, papel, first_name="", last_name=""):
    """Usuário do Controle de Acesso com um papel (Group criado pelas migrações do acesso)."""
    usuario = get_user_model().objects.create_user(
        username, password="Senha-de-teste-123", first_name=first_name, last_name=last_name
    )
    usuario.groups.add(Group.objects.get(name=papel))
    return usuario


class ApiTest(APITestCase):
    def setUp(self):
        services.importar(DADOS, services.Autor())
        self.configurador = _usuario("patricia", "Configurador", "Patrícia", "Gomes Freitas")
        self.cam = _usuario("cam", "CAM/SECOGE")
        self.avaliado = _usuario("ana", "Avaliado")

    def test_formato_igual_ao_front(self):
        self.client.force_authenticate(self.configurador)  # vê o município (ver EscopoTest)
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

    def test_sem_login_nada_e_acessivel(self):
        for rota in ("/api/usuarios/", "/api/unidades/", "/api/distritos/", "/api/vinculos/", "/api/auditoria/"):
            self.assertEqual(self.client.get(rota).status_code, 403, rota)
        r = self.client.post("/api/unidades/", {"nome": "USF Nova", "distritoId": "d1", "tipo": "USF"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_quem_nao_tem_permissao_nao_cadastra(self):
        for usuario in (self.avaliado, self.cam):
            self.client.force_authenticate(usuario)
            r = self.client.post(
                "/api/unidades/", {"nome": "USF Nova", "distritoId": "d1", "tipo": "USF"}, format="json"
            )
            self.assertEqual(r.status_code, 403, usuario.username)
            r = self.client.patch("/api/usuarios/us2/", {"unidadeId": "u3"}, format="json")
            self.assertEqual(r.status_code, 403, usuario.username)
            self.assertEqual(self.client.post("/api/unidades/u1/inativar/").status_code, 403)
        self.assertFalse(Unidade.objects.filter(nome="USF Nova").exists())

    def test_configurador_cadastra_altera_e_inativa(self):
        self.client.force_authenticate(self.configurador)
        r = self.client.post("/api/unidades/", {"nome": "USF Nova", "distritoId": "d2", "tipo": "USF"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["id"], "u5")

        r = self.client.patch("/api/unidades/u5/", {"nome": "USF Nova II"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

        r = self.client.post("/api/unidades/u5/inativar/")
        self.assertEqual(r.data["status"], "Inativo")

        self.assertEqual(self.client.delete("/api/unidades/u5/").status_code, 405)

        reg = registros().filter(operacao="Unidade cadastrada").latest("id")
        self.assertEqual(reg.usuario, "Patrícia Gomes Freitas")
        self.assertEqual(reg.perfil, "Configurador")

    def test_erros_com_nome_do_campo_do_front(self):
        self.client.force_authenticate(self.configurador)
        r = self.client.post(
            "/api/usuarios/", {"nome": "Sem unidade", "email": "su@x.org", "perfilId": "gestor"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("unidadeId", r.data)

    def test_vinculos_para_apuracao(self):
        self.client.force_authenticate(self.configurador)
        r = self.client.get("/api/vinculos/", {"distritoId": "d1"})
        # Ana (u1), Carlos (u2) e Marcela (coordenadora d1). SEAB/Configurador e inativos ficam fora.
        self.assertEqual([v["avaliadoId"] for v in r.data], ["us1", "us2", "us5"])
        r = self.client.get("/api/unidades/u3/vinculos/")
        self.assertEqual([v["nome"] for v in r.data], ["Fernanda Alves Rocha"])

    def test_importar_por_http_exige_as_duas_permissoes(self):
        dados = {"unidades": [{"nome": "CAPS Centro", "distritoId": "d1", "tipo": "CAPS"}]}
        self.client.force_authenticate(self.avaliado)
        self.assertEqual(self.client.post("/api/cadastro/importar/", dados, format="json").status_code, 403)

        self.client.force_authenticate(self.configurador)
        r = self.client.post("/api/cadastro/importar/", dados, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["unidades"], 1)

    def test_auditoria_no_formato_do_front(self):
        self.client.force_authenticate(self.configurador)
        self.client.patch("/api/usuarios/us2/", {"unidadeId": "u3"}, format="json")
        r = self.client.get("/api/auditoria/", {"componente": "cadastro"})
        primeiro = r.data[0]
        self.assertEqual(primeiro["operacao"], "Vínculo alterado")
        self.assertEqual(
            set(primeiro.keys()),
            {"id", "usuario", "data", "horario", "operacao", "registroAfetado", "valorAnterior", "novoValor", "perfil", "localizacao", "componente"},
        )


# Seletor de perfil do protótipo (apps/acesso/autenticacao.py): só vale com DEBUG.
CONFIGURADOR_DEMO = {"HTTP_X_PERFIL": "configurador", "HTTP_X_USUARIO": "Patr%C3%ADcia%20Gomes%20Freitas"}
GESTOR_DEMO = {"HTTP_X_PERFIL": "gestor", "HTTP_X_USUARIO": "Ana"}


@override_settings(DEBUG=True, SGGD_PERFIL_SIMULADO=True)
class PerfilSimuladoTest(APITestCase):
    def setUp(self):
        services.importar(DADOS, services.Autor())

    def test_configurador_do_seletor_cadastra_e_aparece_na_auditoria(self):
        r = self.client.post(
            "/api/unidades/", {"nome": "USF Nova", "distritoId": "d2", "tipo": "USF"}, format="json", **CONFIGURADOR_DEMO
        )
        self.assertEqual(r.status_code, 201, r.data)
        reg = registros().filter(operacao="Unidade cadastrada").latest("id")
        self.assertEqual(reg.usuario, "Patrícia Gomes Freitas")
        self.assertEqual(reg.perfil, "Configurador SAB")

    def test_gestor_do_seletor_le_mas_nao_cadastra(self):
        self.assertEqual(self.client.get("/api/unidades/", **GESTOR_DEMO).status_code, 200)
        r = self.client.post(
            "/api/unidades/", {"nome": "USF Nova", "distritoId": "d1", "tipo": "USF"}, format="json", **GESTOR_DEMO
        )
        self.assertEqual(r.status_code, 403)

    @override_settings(DEBUG=False)
    def test_sem_debug_o_cabecalho_e_ignorado(self):
        self.assertEqual(self.client.get("/api/unidades/", **CONFIGURADOR_DEMO).status_code, 403)

    def test_escopo_do_seletor_e_a_pessoa_que_o_front_usa(self):
        # Mesma pessoa de usuarioDoPerfil() no front: o 1º ativo do perfil (Ana em u1, Marcela em d1).
        esperado = {"gestor": ["u1"], "coordenador": ["u1", "u2"], "seab": ["u1", "u2", "u3", "u4"]}
        for perfil, unidades in esperado.items():
            r = self.client.get("/api/unidades/", HTTP_X_PERFIL=perfil)
            self.assertEqual([u["id"] for u in r.data], unidades, perfil)


def _ids(resposta):
    return [item["id"] if "id" in item else item["avaliadoId"] for item in resposta.data]


class EscopoTest(APITestCase):
    """Cada um vê só o seu escopo (escopo.py), com a mesma regra de frontend/src/utils/escopo.ts."""

    def setUp(self):
        services.importar(DADOS, services.Autor())
        self.configurador = _usuario("diego", "Configurador")
        self.cam_sem_vinculo = _usuario("cam", "CAM/SECOGE")
        self.sem_vinculo = _usuario("sem.vinculo", "Avaliado")
        self.ana = self._ligar(_usuario("ana", "Avaliado"), "us1")  # gestora de u1 (d1)
        self.marcela = self._ligar(_usuario("marcela", "Avaliado"), "us5")  # coordenadora de d1
        self.patricia = self._ligar(_usuario("patricia", "CAM/SECOGE"), "us7")  # SEAB/CAM
        self.luciana = self._ligar(_usuario("luciana", "Avaliado"), "us9")  # coordenadora inativa

    def _ligar(self, login, avaliado_id):
        avaliado = Avaliado.objects.get(pk=avaliado_id)
        avaliado.usuario = login
        services.salvar(avaliado, services.Autor())
        return login

    def _get(self, usuario, rota, **params):
        self.client.force_authenticate(usuario)
        return self.client.get(rota, params)

    def test_gestor_ve_so_a_propria_unidade(self):
        self.assertEqual(_ids(self._get(self.ana, "/api/unidades/")), ["u1"])
        self.assertEqual(_ids(self._get(self.ana, "/api/usuarios/")), ["us1"])
        self.assertEqual(_ids(self._get(self.ana, "/api/distritos/")), ["d1"])
        self.assertEqual(_ids(self._get(self.ana, "/api/vinculos/")), ["us1"])
        self.assertEqual(self._get(self.ana, "/api/unidades/u1/").status_code, 200)
        # Fora do escopo: responde como se não existisse.
        self.assertEqual(self._get(self.ana, "/api/unidades/u2/").status_code, 404)
        self.assertEqual(self._get(self.ana, "/api/unidades/u2/vinculos/").status_code, 404)
        self.assertEqual(self._get(self.ana, "/api/usuarios/us2/").status_code, 404)

    def test_coordenador_ve_o_distrito(self):
        self.assertEqual(_ids(self._get(self.marcela, "/api/unidades/")), ["u1", "u2"])
        self.assertEqual(_ids(self._get(self.marcela, "/api/usuarios/")), ["us1", "us2", "us5"])
        self.assertEqual(_ids(self._get(self.marcela, "/api/vinculos/")), ["us1", "us2", "us5"])
        self.assertEqual(_ids(self._get(self.marcela, "/api/unidades/u2/vinculos/")), ["us2"])
        self.assertEqual(self._get(self.marcela, "/api/unidades/u3/").status_code, 404)
        # Filtro de outro distrito não fura o escopo.
        self.assertEqual(_ids(self._get(self.marcela, "/api/unidades/", distritoId="d2")), [])

    def test_seab_e_configurador_veem_o_municipio(self):
        for usuario in (self.patricia, self.configurador):
            self.assertEqual(len(self._get(usuario, "/api/unidades/").data), 4, usuario.username)
            self.assertEqual(len(self._get(usuario, "/api/usuarios/").data), 9, usuario.username)
            self.assertEqual(len(self._get(usuario, "/api/distritos/").data), 3, usuario.username)

    def test_sem_pessoa_ativa_ligada_nao_ve_nada(self):
        for usuario in (self.cam_sem_vinculo, self.sem_vinculo, self.luciana):
            for rota in ("/api/unidades/", "/api/usuarios/", "/api/distritos/", "/api/vinculos/"):
                r = self._get(usuario, rota)
                self.assertEqual((r.status_code, r.data), (200, []), f"{usuario.username} {rota}")
            self.assertEqual(self._get(usuario, "/api/unidades/u1/").status_code, 404)

    def test_vinculos_de_unidade_inexistente_e_404(self):
        self.assertEqual(self._get(self.configurador, "/api/unidades/u999/vinculos/").status_code, 404)

    def test_configurador_altera_fora_do_proprio_vinculo(self):
        self.client.force_authenticate(self.configurador)
        r = self.client.patch("/api/unidades/u3/", {"nome": "USF Ibura II"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

    def test_interface_para_outros_componentes(self):
        # Como a publicação/coleta usariam: request comum do Django, sem DRF.
        request = RequestFactory().get("/")
        request.user = self.marcela
        escopo = escopo_do_request(request)
        self.assertEqual(escopo.unidade_ids(), ["u1", "u2"])
        self.assertTrue(escopo.alcanca_unidade("u2"))
        self.assertFalse(escopo.alcanca_unidade("u3"))
        request.user = self.sem_vinculo
        self.assertTrue(escopo_do_request(request).vazio)

    def test_vinculos_sem_escopo_continua_completo_para_a_apuracao(self):
        self.assertEqual(len(services.vinculos_unidade_pessoa()), 6)  # 4 gestores + 2 coordenadores ativos
