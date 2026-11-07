from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from .autenticacao import PerfilSimuladoAuthentication
from .interface import ExigePermissao, identificacao, usuario_tem_permissao
from .models import Usuario

# Permissão nativa do próprio app, usada como exemplo de operação protegida.
PERMISSAO = "acesso.view_usuario"


def _permissao(codigo):
    app_label, codename = codigo.split(".")
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def _papel_com(nome, *codigos):
    papel = Group.objects.create(name=nome)
    papel.permissions.add(*(_permissao(c) for c in codigos))
    return papel


class UsuarioTests(TestCase):
    def test_modelo_de_usuario_do_projeto_e_o_do_acesso(self):
        self.assertIs(get_user_model(), Usuario)

    def test_senha_e_armazenada_com_hash(self):
        usuario = Usuario.objects.create_user("ana", password="Senha-de-teste-123")

        self.assertNotIn("Senha-de-teste-123", usuario.password)
        self.assertTrue(usuario.check_password("Senha-de-teste-123"))


# Especificação: responsabilidades de cada ator do diagrama de casos de uso.
PERMISSOES_ESPERADAS = {
    "Técnico": {"registrar_resultado"},
    "Configurador": {
        "cadastrar_indicador",
        "configurar_regra_calculo",
        "cadastrar_unidade",
        "cadastrar_avaliado",
    },
    "CAM/SECOGE": {
        "homologar_resultado",
        "encerrar_ciclo",
        "publicar_resultado",
        "julgar_recurso",
        "enviar_resultado_folha",
    },
    "Avaliado": {"consultar_propria_pontuacao", "apresentar_recurso"},
}


def _usuario_com_papeis(username, *papeis):
    usuario = Usuario.objects.create_user(username, password="Senha-de-teste-123")
    usuario.groups.add(*Group.objects.filter(name__in=papeis))
    return usuario


def _pode(usuario, codename):
    return usuario_tem_permissao(usuario, f"acesso.{codename}")


class PapeisTests(TestCase):
    def test_existem_somente_os_papeis_dos_casos_de_uso(self):
        nomes = set(Group.objects.values_list("name", flat=True))

        # Sem SEGTES (ator externo) e sem perfil genérico de administrador.
        self.assertEqual(nomes, set(PERMISSOES_ESPERADAS))

    def test_cada_papel_tem_exatamente_as_permissoes_das_suas_responsabilidades(self):
        for papel, esperadas in PERMISSOES_ESPERADAS.items():
            with self.subTest(papel=papel):
                grupo = Group.objects.get(name=papel)
                self.assertEqual(set(grupo.permissions.values_list("codename", flat=True)), esperadas)

    def test_catalogo_nao_tem_operacao_de_alterar_pontuacao(self):
        catalogo = set(
            Permission.objects.filter(content_type__model="operacao").values_list("codename", flat=True)
        )

        self.assertEqual(catalogo, set().union(*PERMISSOES_ESPERADAS.values()))


class PermissoesPorPapelTests(TestCase):
    def test_usuario_com_dois_papeis_acumula_as_permissoes(self):
        usuario = _usuario_com_papeis("ana", "Técnico", "Configurador")

        self.assertTrue(_pode(usuario, "registrar_resultado"))
        self.assertTrue(_pode(usuario, "cadastrar_indicador"))
        self.assertFalse(_pode(usuario, "homologar_resultado"))

    def test_tecnico_nao_homologa_nem_publica(self):
        tecnico = _usuario_com_papeis("ana", "Técnico")

        for codename in ("homologar_resultado", "publicar_resultado", "encerrar_ciclo"):
            with self.subTest(codename=codename):
                self.assertFalse(_pode(tecnico, codename))

    def test_configurador_nao_registra_resultado(self):
        configurador = _usuario_com_papeis("ana", "Configurador")

        self.assertFalse(_pode(configurador, "registrar_resultado"))

    def test_avaliado_so_consulta_a_propria_pontuacao_e_apresenta_recurso(self):
        avaliado = _usuario_com_papeis("ana", "Avaliado")
        outras = set().union(*PERMISSOES_ESPERADAS.values()) - PERMISSOES_ESPERADAS["Avaliado"]

        self.assertTrue(_pode(avaliado, "consultar_propria_pontuacao"))
        self.assertTrue(_pode(avaliado, "apresentar_recurso"))
        for codename in sorted(outras):
            with self.subTest(codename=codename):
                self.assertFalse(_pode(avaliado, codename))

    def test_cam_nao_cadastra_indicador_nem_registra_resultado(self):
        cam = _usuario_com_papeis("ana", "CAM/SECOGE")

        self.assertTrue(_pode(cam, "julgar_recurso"))
        self.assertFalse(_pode(cam, "cadastrar_indicador"))
        self.assertFalse(_pode(cam, "registrar_resultado"))

    def test_usuario_sem_papel_nao_executa_nenhuma_operacao(self):
        usuario = _usuario_com_papeis("ana")

        for codename in sorted(set().union(*PERMISSOES_ESPERADAS.values())):
            with self.subTest(codename=codename):
                self.assertFalse(_pode(usuario, codename))


class UsuarioTemPermissaoTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user("ana", password="Senha-de-teste-123")

    def test_usuario_autenticado_sem_permissao_e_negado(self):
        self.assertFalse(usuario_tem_permissao(self.usuario, PERMISSAO))

    def test_permissao_recebida_pelo_papel_e_concedida(self):
        self.usuario.groups.add(_papel_com("Papel de teste", PERMISSAO))

        self.assertTrue(usuario_tem_permissao(self.usuario, PERMISSAO))

    def test_usuario_com_varios_papeis_soma_as_permissoes(self):
        self.usuario.groups.add(
            _papel_com("Papel A", "acesso.view_usuario"),
            _papel_com("Papel B", "acesso.change_usuario"),
        )

        self.assertTrue(usuario_tem_permissao(self.usuario, "acesso.view_usuario"))
        self.assertTrue(usuario_tem_permissao(self.usuario, "acesso.change_usuario"))
        self.assertFalse(usuario_tem_permissao(self.usuario, "acesso.delete_usuario"))

    def test_usuario_inativo_e_negado_mesmo_com_permissao(self):
        self.usuario.user_permissions.add(_permissao(PERMISSAO))
        self.usuario.is_active = False
        self.usuario.save()

        self.assertFalse(usuario_tem_permissao(self.usuario, PERMISSAO))

    def test_usuario_anonimo_e_negado(self):
        self.assertFalse(usuario_tem_permissao(AnonymousUser(), PERMISSAO))
        self.assertFalse(usuario_tem_permissao(None, PERMISSAO))

    def test_superusuario_tem_todas_as_permissoes(self):
        admin = Usuario.objects.create_superuser("admin", password="Senha-de-teste-123")

        self.assertTrue(usuario_tem_permissao(admin, PERMISSAO))


class OperacaoProtegida(APIView):
    permission_classes = [ExigePermissao]
    permissoes_exigidas = (PERMISSAO,)

    def post(self, request):
        return Response({"ok": True})


class OperacaoComDuasPermissoes(OperacaoProtegida):
    permissoes_exigidas = ("acesso.view_usuario", "acesso.change_usuario")


class OperacaoSemPermissaoDeclarada(OperacaoProtegida):
    permissoes_exigidas = ()


class ExigePermissaoTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user("ana", password="Senha-de-teste-123")

    def _post(self, view_class, usuario=None):
        request = APIRequestFactory().post("/operacao/")
        if usuario is not None:
            force_authenticate(request, user=usuario)
        return view_class.as_view()(request)

    def test_usuario_nao_autenticado_e_bloqueado(self):
        resposta = self._post(OperacaoProtegida)

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resposta.data["detail"].code, "not_authenticated")

    def test_usuario_autenticado_sem_permissao_e_bloqueado(self):
        resposta = self._post(OperacaoProtegida, self.usuario)

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resposta.data["detail"].code, "permission_denied")

    def test_usuario_com_permissao_executa_a_operacao(self):
        self.usuario.groups.add(_papel_com("Papel de teste", PERMISSAO))

        resposta = self._post(OperacaoProtegida, self.usuario)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_todas_as_permissoes_exigidas_sao_necessarias(self):
        self.usuario.groups.add(_papel_com("Papel de teste", "acesso.view_usuario"))

        resposta = self._post(OperacaoComDuasPermissoes, self.usuario)

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_sem_permissoes_exigidas_falha_em_vez_de_liberar(self):
        with self.assertRaises(ImproperlyConfigured):
            self._post(OperacaoSemPermissaoDeclarada, self.usuario)


class JulgarRecurso(APIView):
    permission_classes = [ExigePermissao]
    permissoes_exigidas = ("acesso.julgar_recurso",)

    def post(self, request):
        return Response({"ok": True})


class OperacaoPorPapelNaApiTests(TestCase):
    def _post(self, usuario):
        request = APIRequestFactory().post("/recursos/1/julgar/")
        force_authenticate(request, user=usuario)
        return JulgarRecurso.as_view()(request)

    def test_avaliado_nao_julga_recurso(self):
        resposta = self._post(_usuario_com_papeis("ana", "Avaliado"))

        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_cam_secoge_julga_recurso(self):
        resposta = self._post(_usuario_com_papeis("bia", "CAM/SECOGE"))

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)


def _requisicao_demo(**cabecalhos):
    return Request(APIRequestFactory().get("/", **cabecalhos))


@override_settings(DEBUG=True, SGGD_PERFIL_SIMULADO=True)
class PerfilSimuladoTests(TestCase):
    """Modo demonstração do protótipo: X-Perfil vira usuário de demonstração com papel."""

    def autenticar(self, **cabecalhos):
        return PerfilSimuladoAuthentication().authenticate(_requisicao_demo(**cabecalhos))

    def test_perfil_vira_usuario_demo_com_o_papel_equivalente(self):
        esperado = {"configurador": "Configurador", "seab": "CAM/SECOGE", "gestor": "Avaliado", "coordenador": "Avaliado"}
        for perfil, papel in esperado.items():
            usuario, _ = self.autenticar(HTTP_X_PERFIL=perfil)
            self.assertEqual(usuario.username, f"demo-{perfil}")
            self.assertEqual(list(usuario.groups.values_list("name", flat=True)), [papel])
            self.assertFalse(usuario.has_usable_password())

    def test_usuario_demo_e_reaproveitado(self):
        primeiro, _ = self.autenticar(HTTP_X_PERFIL="gestor")
        segundo, _ = self.autenticar(HTTP_X_PERFIL="gestor")
        self.assertEqual(primeiro.pk, segundo.pk)

    def test_permissoes_vem_do_papel(self):
        configurador, _ = self.autenticar(HTTP_X_PERFIL="configurador")
        gestor, _ = self.autenticar(HTTP_X_PERFIL="gestor")
        self.assertTrue(usuario_tem_permissao(configurador, "acesso.cadastrar_unidade"))
        self.assertFalse(usuario_tem_permissao(gestor, "acesso.cadastrar_unidade"))

    def test_identificacao_usa_o_nome_enviado_pelo_front(self):
        requisicao = _requisicao_demo(HTTP_X_PERFIL="seab", HTTP_X_USUARIO="Patr%C3%ADcia")
        usuario, auth = PerfilSimuladoAuthentication().authenticate(requisicao)
        requisicao.user, requisicao.auth = usuario, auth
        self.assertEqual(identificacao(requisicao), ("Patrícia", "seab"))

    def test_perfil_desconhecido_e_recusado(self):
        with self.assertRaises(AuthenticationFailed):
            self.autenticar(HTTP_X_PERFIL="admin")

    def test_sem_cabecalho_nao_autentica(self):
        self.assertIsNone(self.autenticar())

    @override_settings(DEBUG=False)
    def test_sem_debug_nao_autentica(self):
        self.assertIsNone(self.autenticar(HTTP_X_PERFIL="configurador"))

    @override_settings(SGGD_PERFIL_SIMULADO=False)
    def test_desligado_nao_autentica(self):
        self.assertIsNone(self.autenticar(HTTP_X_PERFIL="configurador"))
