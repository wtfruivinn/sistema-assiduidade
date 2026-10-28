import json
from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sistema.models import (
    CategoriaDocente, Docente, Curso, UC, Turma,
    Recinto, Sala, Estudante, Inscricao,
)


class Command(BaseCommand):
    help = "Importa docentes, cursos, UCs, turmas, salas e estudantes de um ficheiro JSON (sem duplicar)."

    def add_arguments(self, parser):
        parser.add_argument("ficheiro", help="Caminho do ficheiro JSON")

    def handle(self, *args, **opcoes):
        caminho = opcoes["ficheiro"]
        try:
            with open(caminho, encoding="utf-8") as f:
                dados = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"Ficheiro não encontrado: {caminho}")
        except json.JSONDecodeError as e:
            raise CommandError(f"JSON inválido: {e}")

        contagem = {}

        def conta(nome, criado):
            c = contagem.setdefault(nome, [0, 0])
            c[0 if criado else 1] += 1

        with transaction.atomic():
            # ---------- Recintos ----------
            recintos = {}
            for r in dados.get("recintos", []):
                obj, criado = Recinto.objects.get_or_create(
                    nome=r["nome"],
                    defaults={
                        "latitude": r["latitude"],
                        "longitude": r["longitude"],
                        "raio_metros": r.get("raio_metros", 300),
                    },
                )
                recintos[obj.nome] = obj
                conta("recintos", criado)

            # ---------- Categorias ----------
            categorias = {}
            for c in dados.get("categorias", []):
                obj = CategoriaDocente.objects.filter(designacao=c["designacao"]).first()
                criado = obj is None
                if criado:
                    obj = CategoriaDocente.objects.create(
                        designacao=c["designacao"],
                        valor_hora=c["valor_hora"],
                        data_inicio=c.get("data_inicio", date(2026, 1, 1)),
                    )
                categorias[obj.designacao] = obj
                conta("categorias", criado)

            # ---------- Docentes (com utilizador) ----------
            for d in dados.get("docentes", []):
                partes = d["nome"].split(" ", 1)
                user, user_criado = User.objects.get_or_create(
                    username=d["username"],
                    defaults={
                        "first_name": partes[0],
                        "last_name": partes[1] if len(partes) > 1 else "",
                    },
                )
                if user_criado:
                    user.set_password(d.get("password", "Teste@2026"))
                    user.save()
                else:
                    user.first_name = partes[0]
                    user.last_name = partes[1] if len(partes) > 1 else ""
                    user.save()

                _, criado = Docente.objects.update_or_create(
                    numero_docente=d["numero_docente"],
                    defaults={
                        "nome": d["nome"],
                        "categoria": categorias.get(d["categoria"])
                        or CategoriaDocente.objects.get(designacao=d["categoria"]),
                        "departamento": d["departamento"],
                        "user": user,
                        "estado": True,
                    },
                )
                conta("docentes", criado)

            # ---------- Cursos ----------
            cursos = {}
            for c in dados.get("cursos", []):
                obj, criado = Curso.objects.update_or_create(
                    codigo=c["codigo"],
                    defaults={
                        "nome": c["nome"],
                        "faculdade": c["faculdade"],
                        "duracao_anos": c.get("duracao_anos", 4),
                    },
                )
                cursos[obj.codigo] = obj
                conta("cursos", criado)

            # ---------- UCs ----------
            ucs = {}
            for u in dados.get("ucs", []):
                obj, criado = UC.objects.update_or_create(
                    codigo=u["codigo"],
                    defaults={
                        "nome": u["nome"],
                        "curso": cursos[u["curso"]],
                        "creditos": u.get("creditos", 6),
                        "carga_horaria": u.get("carga_horaria", 60),
                    },
                )
                ucs[obj.codigo] = obj
                conta("ucs", criado)

            # ---------- Turmas ----------
            turmas = {}
            for t in dados.get("turmas", []):
                obj, criado = Turma.objects.update_or_create(
                    codigo=t["codigo"],
                    defaults={
                        "uc": ucs[t["uc"]],
                        "ano_letivo": t.get("ano_letivo", "2026/2027"),
                        "semestre": t.get("semestre", "1º"),
                        "capacidade": t.get("capacidade", 50),
                        "estado": True,
                    },
                )
                turmas[obj.codigo] = obj
                conta("turmas", criado)

            # ---------- Salas ----------
            for s in dados.get("salas", []):
                obj, criado = Sala.objects.get_or_create(
                    codigo=s["codigo"],
                    defaults={
                        "edificio": s["edificio"],
                        "piso": s.get("piso", "0"),
                        "recinto": recintos.get(s.get("recinto")),
                        "latitude": s.get("latitude"),
                        "longitude": s.get("longitude"),
                        "qr_code": s.get("qr_code", ""),
                        "wifi_ssid": s.get("wifi_ssid", ""),
                    },
                )
                conta("salas", criado)

            # ---------- Estudantes + inscrições ----------
            for e in dados.get("estudantes", []):
                est, criado = Estudante.objects.update_or_create(
                    numero_estudante=e["numero_estudante"],
                    defaults={
                        "nome": e["nome"],
                        "curso": cursos[e["curso"]],
                        "ano_ingresso": e.get("ano_ingresso", 2024),
                        "email": e.get("email", ""),
                        "estado": True,
                    },
                )
                conta("estudantes", criado)
                for cod_turma in e.get("turmas", []):
                    _, insc_criada = Inscricao.objects.get_or_create(
                        estudante=est, turma=turmas[cod_turma]
                    )
                    conta("inscricoes", insc_criada)

        self.stdout.write(self.style.SUCCESS("Importação concluída."))
        for nome, (novos, existentes) in contagem.items():
            self.stdout.write(f"  {nome}: {novos} novos, {existentes} já existiam (atualizados)")
