import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Cria os grupos Coordenacao e RH, repõe a password dos docentes de demonstração "
        "e cria os utilizadores 'coordenacao' e 'rh_user'. As passwords vêm de variáveis de "
        "ambiente (DEMO_PASSWORD, COORDENACAO_PASSWORD, RH_PASSWORD), nunca do código."
    )

    def handle(self, *args, **options):
        # 1. Grupos
        for nome in ("Coordenacao", "RH"):
            Group.objects.get_or_create(name=nome)
        self.stdout.write("Grupos Coordenacao e RH garantidos.")

        # 2. Password de todos os docentes de demonstração (docente2026XXXX)
        senha_docentes = os.environ.get("DEMO_PASSWORD")
        if senha_docentes:
            total = 0
            for utilizador in User.objects.filter(username__startswith="docente"):
                utilizador.set_password(senha_docentes)
                utilizador.save()
                total += 1
            self.stdout.write(f"Password reposta para {total} docentes.")
        else:
            self.stdout.write("DEMO_PASSWORD não definida: passwords dos docentes não alteradas.")

        # 3. Utilizadores da coordenação e do RH
        for username, grupo, variavel in (
            ("coordenacao", "Coordenacao", "COORDENACAO_PASSWORD"),
            ("rh_user", "RH", "RH_PASSWORD"),
        ):
            senha = os.environ.get(variavel)
            if not senha:
                self.stdout.write(f"{variavel} não definida: utilizador '{username}' não criado.")
                continue
            utilizador, criado = User.objects.get_or_create(username=username)
            utilizador.set_password(senha)
            utilizador.save()
            utilizador.groups.add(Group.objects.get(name=grupo))
            estado = "criado" if criado else "atualizado"
            self.stdout.write(f"Utilizador '{username}' {estado} no grupo {grupo}.")
