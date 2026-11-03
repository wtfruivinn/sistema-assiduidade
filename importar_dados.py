import os
import django
import json

# Configura o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from sistema.models import (
    Recinto, CategoriaDocente, Docente, Curso, UC, Turma, Sala, Estudante, Inscricao
)

def run():
    print("A ler o ficheiro dados_demo.json...")
    try:
        with open("dados_demo.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
    except FileNotFoundError:
        print("❌ Erro: dados_demo.json não encontrado. Corra o gerar_dados.py primeiro.")
        return

    print("A gravar dados na base de dados...")

    # 1. Recinto
    rec_db, _ = Recinto.objects.get_or_create(
        nome=dados["recintos"][0]["nome"],
        defaults={
            "latitude": dados["recintos"][0]["latitude"],
            "longitude": dados["recintos"][0]["longitude"],
            "raio_metros": dados["recintos"][0]["raio_metros"]
        }
    )

    # 2. Categorias
    cat_map = {}
    for c in dados["categorias"]:
        cat_db, _ = CategoriaDocente.objects.get_or_create(
            designacao=c["designacao"],
            defaults={"valor_hora": c["valor_hora"], "data_inicio": c["data_inicio"]}
        )
        cat_map[c["designacao"]] = cat_db

    # 3. Cursos
    curso_map = {}
    for c in dados["cursos"]:
        cur_db, _ = Curso.objects.get_or_create(
            codigo=c["codigo"],
            defaults={"nome": c["nome"], "faculdade": c["faculdade"], "duracao_anos": c["duracao_anos"]}
        )
        curso_map[c["codigo"]] = cur_db

    # 4. UCs e Turmas
    uc_map = {}
    turma_map = {}
    for u in dados["ucs"]:
        uc_db, _ = UC.objects.get_or_create(
            codigo=u["codigo"],
            defaults={"nome": u["nome"], "curso": curso_map[u["curso"]], "creditos": u["creditos"], "carga_horaria": u["carga_horaria"]}
        )
        uc_map[u["codigo"]] = uc_db

    for t in dados["turmas"]:
        tur_db, _ = Turma.objects.get_or_create(
            codigo=t["codigo"],
            defaults={"uc": uc_map[t["uc"]], "ano_letivo": t["ano_letivo"], "semestre": t["semestre"], "capacidade": t["capacidade"]}
        )
        turma_map[t["codigo"]] = tur_db

    # 5. Salas
    for s in dados["salas"]:
        Sala.objects.get_or_create(
            codigo=s["codigo"],
            defaults={
                "edificio": s["edificio"], "piso": s["piso"], "recinto": rec_db,
                "latitude": s["latitude"], "longitude": s["longitude"], "qr_code": s["qr_code"]
            }
        )

    # 6. Docentes (e os respetivos Users)
    for d in dados["docentes"]:
        user, _ = User.objects.get_or_create(username=d["username"])
        user.set_password(d["password"])
        user.save()

        Docente.objects.get_or_create(
            numero_docente=d["numero_docente"],
            defaults={
                "user": user, "nome": d["nome"], "categoria": cat_map[d["categoria"]],
                "departamento": d["departamento"], "estado": True
            }
        )

    # 7. Estudantes (e Inscrições)
    for e in dados["estudantes"]:
        est_db, _ = Estudante.objects.get_or_create(
            numero_estudante=e["numero_estudante"],
            defaults={"nome": e["nome"], "curso": curso_map[e["curso"]], "ano_ingresso": e["ano_ingresso"], "email": e["email"]}
        )
        for t_cod in e["turmas"]:
            if t_cod in turma_map:
                Inscricao.objects.get_or_create(estudante=est_db, turma=turma_map[t_cod])

    print("🎉 Dados gravados com sucesso na base de dados!")

if __name__ == '__main__':
    run()