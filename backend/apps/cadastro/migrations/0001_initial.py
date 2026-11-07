import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Distrito",
            fields=[
                ("id", models.CharField(blank=True, max_length=40, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=100, unique=True)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Unidade",
            fields=[
                ("id", models.CharField(blank=True, max_length=40, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=200)),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("USF", "USF"),
                            ("UBT", "UBT"),
                            ("UPA", "UPA"),
                            ("Policlínica", "Policlínica"),
                            ("CAPS", "CAPS"),
                            ("Outro", "Outro"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "cnes",
                    models.CharField(
                        blank=True,
                        max_length=7,
                        null=True,
                        unique=True,
                        validators=[django.core.validators.RegexValidator("^\\d{7}$", "O CNES deve ter 7 dígitos.")],
                        verbose_name="CNES",
                    ),
                ),
                (
                    "status",
                    models.CharField(choices=[("Ativo", "Ativo"), ("Inativo", "Inativo")], default="Ativo", max_length=10),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "distrito",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name="unidades", to="cadastro.distrito"
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
                "constraints": [
                    models.UniqueConstraint(fields=("distrito", "nome"), name="unidade_nome_unico_no_distrito")
                ],
            },
        ),
        migrations.CreateModel(
            name="Avaliado",
            fields=[
                ("id", models.CharField(blank=True, max_length=40, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=200)),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="e-mail")),
                (
                    "matricula",
                    models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name="matrícula"),
                ),
                (
                    "perfil",
                    models.CharField(
                        choices=[
                            ("gestor", "Gestor de Unidade"),
                            ("coordenador", "Coordenador Distrital"),
                            ("seab", "SEAB/CAM — Monitoramento"),
                            ("configurador", "Configurador SAB"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(choices=[("Ativo", "Ativo"), ("Inativo", "Inativo")], default="Ativo", max_length=10),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "distrito",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="avaliados",
                        to="cadastro.distrito",
                    ),
                ),
                (
                    "unidade",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="avaliados",
                        to="cadastro.unidade",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
    ]
