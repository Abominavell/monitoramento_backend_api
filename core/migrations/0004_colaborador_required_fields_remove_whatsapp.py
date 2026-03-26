from datetime import date

import django.db.models.deletion
from django.db import migrations, models


def preencher_dados_colaborador(apps, schema_editor):
    Colaborador = apps.get_model("core", "Colaborador")
    Setor = apps.get_model("core", "Setor")

    setor_padrao, _ = Setor.objects.get_or_create(nome="Sem setor")

    Colaborador.objects.filter(setor__isnull=True).update(setor=setor_padrao)
    Colaborador.objects.filter(models.Q(cpf__isnull=True) | models.Q(cpf="")).update(cpf="000.000.000-00")
    Colaborador.objects.filter(data_nascimento__isnull=True).update(data_nascimento=date(1900, 1, 1))


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_colaborador_cpf_colaborador_data_nascimento"),
    ]

    operations = [
        migrations.RunPython(preencher_dados_colaborador, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="colaborador",
            name="setor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="colaboradores",
                to="core.setor",
            ),
        ),
        migrations.AlterField(
            model_name="colaborador",
            name="cpf",
            field=models.CharField(max_length=14),
        ),
        migrations.AlterField(
            model_name="colaborador",
            name="data_nascimento",
            field=models.DateField(),
        ),
        migrations.RemoveField(
            model_name="colaborador",
            name="whatsapp",
        ),
    ]
