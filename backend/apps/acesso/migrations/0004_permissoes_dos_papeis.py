from django.contrib.auth.management import create_permissions
from django.db import migrations

# Responsabilidades de cada ator do diagrama de casos de uso (Elicitação de
# Requisitos). A SEGTES é ator externo e não recebe papel. Nenhum papel recebe
# permissão para alterar pontuação diretamente: ela é calculada pela apuração.
PERMISSOES_POR_PAPEL = {
    "Técnico": ["registrar_resultado"],
    "Configurador": [
        "cadastrar_indicador",
        "configurar_regra_calculo",
        "cadastrar_unidade",
        "cadastrar_avaliado",
    ],
    "CAM/SECOGE": [
        "homologar_resultado",
        "encerrar_ciclo",
        "publicar_resultado",
        "julgar_recurso",
        "enviar_resultado_folha",
    ],
    "Avaliado": ["consultar_propria_pontuacao", "apresentar_recurso"],
}


def _permissoes(apps, codenames):
    # Em banco novo as permissões só são criadas após todas as migrações
    # (sinal post_migrate); aqui elas precisam existir antes.
    app_config = apps.get_app_config("acesso")
    app_config.models_module = True
    create_permissions(app_config, verbosity=0, apps=apps)
    app_config.models_module = None

    Permission = apps.get_model("auth", "Permission")
    encontradas = Permission.objects.filter(content_type__app_label="acesso", codename__in=codenames)
    if encontradas.count() != len(codenames):
        raise RuntimeError(f"Permissões do catálogo não encontradas: {codenames}")
    return encontradas


def atribuir(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for papel, codenames in PERMISSOES_POR_PAPEL.items():
        grupo, _ = Group.objects.get_or_create(name=papel)
        grupo.permissions.add(*_permissoes(apps, codenames))


def remover(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for papel, codenames in PERMISSOES_POR_PAPEL.items():
        for grupo in Group.objects.filter(name=papel):
            grupo.permissions.remove(*_permissoes(apps, codenames))


class Migration(migrations.Migration):

    dependencies = [
        ("acesso", "0003_operacoes"),
    ]

    operations = [
        migrations.RunPython(atribuir, remover),
    ]
