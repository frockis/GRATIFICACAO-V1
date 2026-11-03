from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Usuário do sistema (AUTH_USER_MODEL).

    Ainda igual ao User padrão do Django. Foi criado antes da primeira migração
    para que campos vindos da autenticação institucional (ainda não definida)
    possam ser adicionados depois sem trocar o modelo de usuário.

    Papéis são Groups do Django e operações são Permissions; não há campo de
    papel aqui porque uma mesma pessoa pode exercer vários papéis.
    """

    class Meta(AbstractUser.Meta):
        verbose_name = "usuário"
        verbose_name_plural = "usuários"


class Operacao(models.Model):
    """Catálogo das operações protegidas do SGGD.

    Não tem tabela: existe só para declarar as Permissions ("acesso.<codename>")
    que os componentes exigem nas suas views e services. A operação em si é
    implementada pelo componente dono (indicado em cada item).
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            # Técnico
            ("registrar_resultado", "Registrar resultados dos indicadores (UC01, coleta)"),
            # Configurador
            ("cadastrar_indicador", "Cadastrar indicadores (UC02, normativa)"),
            ("configurar_regra_calculo", "Configurar regras de cálculo dos indicadores (UC02, normativa)"),
            ("cadastrar_unidade", "Cadastrar unidades avaliadas (cadastro)"),
            ("cadastrar_avaliado", "Cadastrar avaliados e vinculá-los à unidade (cadastro)"),
            # CAM/SECOGE
            ("homologar_resultado", "Conferir e homologar ou devolver resultados (UC03, apuracao)"),
            ("encerrar_ciclo", "Encerrar o ciclo de avaliação (apuracao)"),
            ("publicar_resultado", "Publicar o resultado (UC04, publicacao)"),
            ("julgar_recurso", "Julgar recursos (UC05, recurso)"),
            ("enviar_resultado_folha", "Enviar resultados aprovados para a folha (UC06, pagamento)"),
            # Avaliado
            ("consultar_propria_pontuacao", "Consultar a própria pontuação (UC07, publicacao)"),
            ("apresentar_recurso", "Apresentar recurso (UC08, recurso)"),
        ]
