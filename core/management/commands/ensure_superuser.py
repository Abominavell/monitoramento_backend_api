import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Cria um superusuário a partir das variáveis de ambiente se ainda não existir "
        "nenhum usuário (útil no Render sem Shell). "
        "Defina BOOTSTRAP_SUPERUSER_USERNAME e BOOTSTRAP_SUPERUSER_PASSWORD."
    )

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write("Usuários já existem; nada a fazer.")
            return

        username = (os.environ.get("BOOTSTRAP_SUPERUSER_USERNAME") or "").strip()
        password = os.environ.get("BOOTSTRAP_SUPERUSER_PASSWORD") or ""

        if not username or not password:
            self.stdout.write(
                "BOOTSTRAP_SUPERUSER_USERNAME/PASSWORD não definidos; "
                "pule ou crie o admin manualmente."
            )
            return

        email = (os.environ.get("BOOTSTRAP_SUPERUSER_EMAIL") or "").strip()
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f"Superusuário {username!r} criado."))
