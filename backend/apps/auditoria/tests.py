from django.contrib.auth import get_user_model
from django.test import TestCase

from .interface import consultar, registrar
from .models import RegistroAuditoria


class RegistrarTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("ana", password="Senha-de-teste-123")

    def test_registrar_grava_o_fato_e_o_nome_do_usuario(self):
        registrar(
            usuario=self.usuario,
            operacao="cadastrar_indicador",
            entidade="indicador",
            identificador="CAM-1.2/1",
            valor_novo='{"codigo": "1"}',
        )

        registro = RegistroAuditoria.objects.get()
        self.assertEqual(registro.usuario_id, self.usuario.id)
        self.assertEqual(registro.usuario_identificacao, "ana")
        self.assertEqual(registro.operacao, "cadastrar_indicador")

    def test_consultar_devolve_o_que_foi_registrado(self):
        registrar(
            usuario=self.usuario,
            operacao="cadastrar_normativa",
            entidade="normativa",
            identificador="CAM-1.2",
            valor_novo="{}",
        )

        encontrados = consultar(entidade="normativa", identificador="CAM-1.2")

        self.assertEqual(len(encontrados), 1)
        self.assertEqual(encontrados[0].operacao, "cadastrar_normativa")

    def test_sem_usuario_autenticado_nao_registra(self):
        with self.assertRaises(ValueError):
            registrar(
                usuario=None,
                operacao="cadastrar_indicador",
                entidade="indicador",
                identificador="1",
            )

        self.assertEqual(RegistroAuditoria.objects.count(), 0)
