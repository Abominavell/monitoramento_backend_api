from django.contrib.auth.hashers import make_password
from django.db import migrations


def sync_sede_users(apps, schema_editor):
    Colaborador = apps.get_model("core", "Colaborador")
    User = apps.get_model("auth", "User")

    for colaborador in Colaborador.objects.filter(is_externo=False).exclude(cpf__isnull=True).exclude(cpf=""):
        if not colaborador.data_nascimento:
            continue

        senha = colaborador.data_nascimento.strftime("%d%m%Y")
        user, _ = User.objects.get_or_create(
            username=colaborador.cpf,
            defaults={
                "first_name": colaborador.nome[:150],
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
            },
        )
        user.first_name = colaborador.nome[:150]
        user.is_active = True
        user.password = make_password(senha)
        user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_alter_colaborador_cpf"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(sync_sede_users, migrations.RunPython.noop),
    ]
