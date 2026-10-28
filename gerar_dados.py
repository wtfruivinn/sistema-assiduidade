"""
Gera o ficheiro dados_demo.json com dados FICTÍCIOS de demonstração:
20 docentes, 5 cursos, 36 UCs, 36 turmas, 30 salas e 500 estudantes.

Uso (na pasta ~/sistema-assiduidade):
    python gerar_dados.py
"""
import json
import random

random.seed(2026)  # mesmos dados sempre que correres o script

RECINTO = "Campus Universidade Zambeze"
LAT0, LON0 = -19.8321630, 34.8648910  # centro do campus (SALA-102)
PASSWORD = "Teste@2026"
ANO_LETIVO = "2026/2027"

# ------------------------------------------------------------
# Categorias
# ------------------------------------------------------------
UNIV = "Assistente Universitário"
SENIOR = "Assistente Universitário Sénior"
DOUTOR = "Professor Doutor"

categorias = [
    {"designacao": UNIV, "valor_hora": 650, "data_inicio": "2026-01-01"},
    {"designacao": SENIOR, "valor_hora": 750, "data_inicio": "2026-01-01"},
    {"designacao": DOUTOR, "valor_hora": 950, "data_inicio": "2026-01-01"},
]

# ------------------------------------------------------------
# Cursos e UCs
# ------------------------------------------------------------
cursos_def = [
    ("INF", "Engenharia Informática", "FCT", "Informática", [
        "Programação II", "Análise Matemática", "Microprocessadores",
        "Estruturas de Dados e Algoritmos", "Redes de Comunicações",
        "Engenharia de Software", "Compiladores", "Gestão Económica e Financeira",
    ]),
    ("DIR", "Direito", "FD", "Direito", [
        "Introdução ao Estudo do Direito", "Direito Constitucional", "Direito Civil I",
        "Direito Penal", "Direito Administrativo", "Direito Comercial", "Direito do Trabalho",
    ]),
    ("GES", "Gestão", "FCSH", "Gestão", [
        "Introdução à Gestão", "Contabilidade Geral", "Marketing",
        "Gestão de Recursos Humanos", "Matemática Financeira", "Direito Comercial",
        "Gestão de Projectos",
    ]),
    ("CAU", "Contabilidade e Auditoria", "FCSH", "Contabilidade", [
        "Contabilidade Financeira I", "Contabilidade Analítica", "Fiscalidade",
        "Auditoria Financeira", "Análise de Demonstrações Financeiras",
        "Direito Fiscal", "Controlo Interno",
    ]),
    ("ECO", "Economia", "FCSH", "Economia", [
        "Microeconomia", "Macroeconomia", "Estatística Económica",
        "Economia de Moçambique", "Economia Internacional", "Econometria",
        "Finanças Públicas",
    ]),
]

cursos, ucs, turmas = [], [], []
ucs_por_curso = {}
for cod, nome, fac, _dep, lista in cursos_def:
    cursos.append({"codigo": cod, "nome": nome, "faculdade": fac, "duracao_anos": 4})
    ucs_por_curso[cod] = []
    for i, nome_uc in enumerate(lista, start=1):
        cod_uc = f"{cod}{100 + i}"
        ucs.append({"codigo": cod_uc, "nome": nome_uc, "curso": cod,
                    "creditos": 6, "carga_horaria": 60})
        turmas.append({"codigo": f"T-{cod_uc}", "uc": cod_uc,
                       "ano_letivo": ANO_LETIVO,
                       "semestre": "1º" if i % 2 else "2º",
                       "capacidade": 80})
        ucs_por_curso[cod].append(f"T-{cod_uc}")

# ------------------------------------------------------------
# Docentes (personagens de ficção)
# ------------------------------------------------------------
docentes_def = [
    # Informática
    ("Anakin Skywalker", "Informática", SENIOR),
    ("Tony Stark", "Informática", DOUTOR),
    ("Thomas Anderson", "Informática", UNIV),
    ("Marty McFly", "Informática", UNIV),
    # Direito
    ("Atticus Finch", "Direito", DOUTOR),
    ("Elle Woods", "Direito", SENIOR),
    ("Harvey Specter", "Direito", SENIOR),
    ("Saul Goodman", "Direito", UNIV),
    # Gestão
    ("Don Draper", "Gestão", DOUTOR),
    ("Leslie Knope", "Gestão", SENIOR),
    ("Michael Scott", "Gestão", UNIV),
    ("Tyrion Lannister", "Gestão", UNIV),
    # Contabilidade
    ("Scrooge McDuck", "Contabilidade", DOUTOR),
    ("Eugene Krabs", "Contabilidade", SENIOR),
    ("Squidward Tentacles", "Contabilidade", UNIV),
    ("Oscar Martinez", "Contabilidade", UNIV),
    # Economia
    ("Bruce Wayne", "Economia", DOUTOR),
    ("Lisa Simpson", "Economia", SENIOR),
    ("Hermione Granger", "Economia", SENIOR),
    ("Sheldon Cooper", "Economia", UNIV),
]
docentes = []
for i, (nome, dep, cat) in enumerate(docentes_def, start=1):
    docentes.append({
        "numero_docente": f"DOC{i:03d}",
        "nome": nome,
        "categoria": cat,
        "departamento": dep,
        "username": f"docente2026{i:04d}",
        "password": PASSWORD,
    })

# ------------------------------------------------------------
# Salas (30)
# ------------------------------------------------------------
salas_def = (
    [(f"NE-{n}", "Novo Edifício", "1" if n < 106 else "2") for n in range(101, 111)]
    + [(f"AE-{n}", "Antigo Edifício", "1" if n < 106 else "2") for n in range(101, 111)]
    + [(f"FD-{n}", "Faculdade de Direito", "1" if n < 104 else "2") for n in range(101, 108)]
    + [("ANF-A", "Anfiteatros", "0"), ("ANF-B", "Anfiteatros", "0"), ("ANF-C", "Anfiteatros", "0")]
)
salas = []
for cod, edificio, piso in salas_def:
    salas.append({
        "codigo": cod,
        "edificio": edificio,
        "piso": piso,
        "recinto": RECINTO,
        # posição dentro de ~45 m do centro do campus
        "latitude": round(LAT0 + random.uniform(-0.0004, 0.0004), 7),
        "longitude": round(LON0 + random.uniform(-0.0004, 0.0004), 7),
        "qr_code": f"QR-{cod}",
    })

# ------------------------------------------------------------
# Estudantes (500 = 25 nomes x 20 apelidos, todos diferentes)
# ------------------------------------------------------------
primeiros = ["Luke", "Leia", "Han", "Rey", "Finn", "Naruto", "Sasuke", "Sakura", "Goku",
             "Vegeta", "Luffy", "Zoro", "Nami", "Harry", "Ron", "Frodo", "Sam", "Aragorn",
             "Simba", "Nala", "Mario", "Link", "Zelda", "Ash", "Misty"]
apelidos = ["Uzumaki", "Uchiha", "Haruno", "Monkey", "Roronoa", "Potter", "Weasley",
            "Baggins", "Gamgee", "Kenobi", "Organa", "Solo", "Ketchum", "Brown",
            "Hyrule", "Kusanagi", "Dragon", "Lion", "Skyrunner", "Starfall"]
combos = [f"{p} {a}" for p in primeiros for a in apelidos]
random.shuffle(combos)

codigos_cursos = [c[0] for c in cursos_def]
estudantes = []
for idx in range(500):
    curso = codigos_cursos[idx % 5]          # 100 por curso
    lista_turmas = ucs_por_curso[curso]
    n = len(lista_turmas)
    ini = (idx // 5) % n
    inscritas = [lista_turmas[(ini + k) % n] for k in range(4)]  # 4 UCs por estudante
    numero = f"E{idx + 1:04d}"
    estudantes.append({
        "numero_estudante": numero,
        "nome": combos[idx],
        "curso": curso,
        "ano_ingresso": random.choice([2023, 2024, 2025, 2026]),
        "email": f"{numero.lower()}@exemplo.test",
        "turmas": inscritas,
    })

# ------------------------------------------------------------
# Ficheiro final
# ------------------------------------------------------------
dados = {
    "recintos": [{"nome": RECINTO, "latitude": LAT0, "longitude": LON0, "raio_metros": 300}],
    "categorias": categorias,
    "docentes": docentes,
    "cursos": cursos,
    "ucs": ucs,
    "turmas": turmas,
    "salas": salas,
    "estudantes": estudantes,
}

with open("dados_demo.json", "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

print("dados_demo.json criado:")
for chave, valor in dados.items():
    print(f"  {chave}: {len(valor)}")
