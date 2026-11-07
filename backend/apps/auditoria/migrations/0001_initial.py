from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RegistroAuditoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data_hora", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "componente",
                    models.CharField(help_text="App que gerou o registro (ex.: cadastro).", max_length=30),
                ),
                ("usuario", models.CharField(max_length=200)),
                ("perfil", models.CharField(blank=True, max_length=60)),
                ("operacao", models.CharField(max_length=100)),
                ("registro_afetado", models.CharField(max_length=300)),
                ("valor_anterior", models.TextField(blank=True)),
                ("novo_valor", models.TextField(blank=True)),
                ("localizacao", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "verbose_name": "registro de auditoria",
                "verbose_name_plural": "registros de auditoria",
                "ordering": ["-data_hora", "-id"],
            },
        ),
    ]
