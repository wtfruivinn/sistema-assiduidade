import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Cria ou atualiza o superuser lendo as variáveis de ambiente "
        "ADMIN_USERNAME (opcional, por defeito 'admin'), ADMIN_EMAIL (opcional) "
        "e ADMIN_PASSWORD (obrigatória). Pode correr várias vezes sem problema."
    )

    def handle(self, *args, **opcoes):
        username = os.environ.get("ADMIN_USERNAME", "admin")
        email = os.environ.get("ADMIN_EMAIL", "")
        password = os.environ.get("ADMIN_PASSWORD")

        if not password:
            raise CommandError(
                "Falta a variável de ambiente ADMIN_PASSWORD. "
                "Defina-a no Render (separador Environment)."
            )

        User = get_user_model()
        user, criado = User.objects.get_or_create(
            username=username, defaults={"email": email}
        )
        if email:
            user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        acao = "criado" if criado else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' {acao}."))
