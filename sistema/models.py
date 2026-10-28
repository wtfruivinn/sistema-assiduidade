from django.db import models
from django.contrib.auth.models import User
 
 
# ============================================================
# CATEGORIAS DE DOCENTES
# ============================================================
class CategoriaDocente(models.Model):
    designacao = models.CharField(max_length=100)
    valor_hora = models.DecimalField(max_digits=10, decimal_places=2)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
 
    class Meta:
        verbose_name = "Categoria de Docente"
        verbose_name_plural = "Categorias de Docentes"
 
    def __str__(self):
        return f"{self.designacao} - {self.valor_hora} MT/h"
 
 
# ============================================================
# DOCENTES
# ============================================================
class Docente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    numero_docente = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    categoria = models.ForeignKey(CategoriaDocente, on_delete=models.PROTECT)
    departamento = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)
 
    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
 
    def __str__(self):
        return f"{self.numero_docente} - {self.nome}"
 
 
# ============================================================
# CURSOS
# ============================================================
class Curso(models.Model):
    FACULDADES = [
        ("FCT", "Faculdade de Ciências e Tecnologia"),
        ("FCSH", "Faculdade de Ciências Sociais e Humanidades"),
        ("FD", "Faculdade de Direito"),
    ]
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    faculdade = models.CharField(max_length=10, choices=FACULDADES, default="FCT")
    duracao_anos = models.IntegerField()
    estado = models.BooleanField(default=True)
 
    def __str__(self):
        return self.nome
 
 
# ============================================================
# UNIDADES CURRICULARES (UCs)
# ============================================================
class UC(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    creditos = models.IntegerField()
    carga_horaria = models.IntegerField(help_text="Horas totais")
 
    class Meta:
        verbose_name = "Unidade Curricular"
        verbose_name_plural = "Unidades Curriculares"
 
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
 
 
# ============================================================
# TURMAS
# ============================================================
class Turma(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    uc = models.ForeignKey(UC, on_delete=models.CASCADE)
    ano_letivo = models.CharField(max_length=10)  # Ex: "2025/2026"
    semestre = models.CharField(max_length=10)    # Ex: "1º"
    capacidade = models.IntegerField()
    estado = models.BooleanField(default=True)
 
    def __str__(self):
        return f"{self.codigo} - {self.uc.nome} ({self.ano_letivo})"
 
 
# ============================================================
# RECINTOS (campus)
# ============================================================
class Recinto(models.Model):
    nome = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    raio_metros = models.IntegerField(default=300, help_text="Raio do recinto em metros")
    estado = models.BooleanField(default=True)
 
    class Meta:
        verbose_name = "Recinto"
        verbose_name_plural = "Recintos"
 
    def __str__(self):
        return f"{self.nome} (raio {self.raio_metros} m)"
 
 
# ============================================================
# SALAS
# ============================================================
class Sala(models.Model):
    EDIFICIOS = [
        ("Novo Edifício", "Novo Edifício"),
        ("Antigo Edifício", "Antigo Edifício"),
        ("Faculdade de Direito", "Faculdade de Direito"),
        ("Anfiteatros", "Anfiteatros"),
    ]
    codigo = models.CharField(max_length=20, unique=True)
    edificio = models.CharField(max_length=100, choices=EDIFICIOS)
    piso = models.CharField(max_length=10)
    recinto = models.ForeignKey(Recinto, on_delete=models.PROTECT, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    qr_code = models.CharField(max_length=100, blank=True, help_text="Código QR da sala")
    wifi_ssid = models.CharField(max_length=100, blank=True)
    ip_subnet = models.CharField(max_length=50, blank=True, help_text="Ex: 192.168.10.0/24")
    beacon_id = models.CharField(max_length=100, blank=True)
    estado = models.BooleanField(default=True)
 
    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
 
    def __str__(self):
        return f"{self.codigo} - {self.edificio} (Piso {self.piso})"
 
 
# ============================================================
# ESTUDANTES
# ============================================================
class Estudante(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    numero_estudante = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT)
    ano_ingresso = models.IntegerField()
    email = models.EmailField(blank=True)
    estado = models.BooleanField(default=True)
 
    class Meta:
        verbose_name = "Estudante"
        verbose_name_plural = "Estudantes"
 
    def __str__(self):
        return f"{self.numero_estudante} - {self.nome}"
 
 
# ============================================================
# INSCRIÇÕES
# ============================================================
class Inscricao(models.Model):
    estudante = models.ForeignKey(Estudante, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    data_inscricao = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, default="ativa")
 
    class Meta:
        unique_together = ("estudante", "turma")
 
    def __str__(self):
        return f"{self.estudante.nome} → {self.turma.codigo}"
 
 
# ============================================================
# HORÁRIOS
# ============================================================
class Horario(models.Model):
    DIAS_SEMANA = [
        ("SEG", "Segunda-feira"),
        ("TER", "Terça-feira"),
        ("QUA", "Quarta-feira"),
        ("QUI", "Quinta-feira"),
        ("SEX", "Sexta-feira"),
        ("SAB", "Sábado"),
    ]
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT)
    sala = models.ForeignKey(Sala, on_delete=models.PROTECT)
    dia_semana = models.CharField(max_length=3, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    ano_letivo = models.CharField(max_length=10)
    semestre = models.CharField(max_length=10)
 
    def __str__(self):
        return f"{self.turma.codigo} - {self.dia_semana} {self.hora_inicio}-{self.hora_fim}"
 
 
# ============================================================
# AULAS
# ============================================================
class Aula(models.Model):
    ESTADOS = [
        ("agendada", "Agendada"),
        ("em_curso", "Em curso"),
        ("validada", "Validada"),
        ("bloqueada", "Bloqueada"),
        ("cancelada", "Cancelada"),
    ]
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT)
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT)
    uc = models.ForeignKey(UC, on_delete=models.PROTECT)
    sala = models.ForeignKey(Sala, on_delete=models.PROTECT)
    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    sumario = models.TextField(blank=True)
    tema = models.CharField(max_length=200, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="agendada")
    hora_inicio_real = models.TimeField(null=True, blank=True)
    hora_fim_real = models.TimeField(null=True, blank=True)
 
    class Meta:
        verbose_name = "Aula"
        verbose_name_plural = "Aulas"
 
    def __str__(self):
        return f"{self.turma.codigo} - {self.data} ({self.estado})"
 
 
# ============================================================
# VALIDAÇÃO DA AULA
# ============================================================
class ValidacaoAula(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name="validacoes")
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT)
    data_hora = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    sala_validada = models.BooleanField(default=False)
    recinto_validado = models.BooleanField(default=False)
    horario_validado = models.BooleanField(default=False)
    qr_validado = models.BooleanField(default=False)
    resultado = models.CharField(max_length=20, help_text="autorizado | bloqueado")
 
    def __str__(self):
        return f"Validação {self.aula} → {self.resultado}"
 
 
# ============================================================
# PRESENÇAS
# ============================================================
class Presenca(models.Model):
    ESTADOS = [
        ("presente", "Presente"),
        ("falta", "Falta"),
        ("falta_justificada", "Falta Justificada"),
    ]
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name="presencas")
    estudante = models.ForeignKey(Estudante, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS)
    data_hora = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        unique_together = ("aula", "estudante")
 
    def __str__(self):
        return f"{self.estudante.nome} - {self.estado}"
 
 
# ============================================================
# HORAS DOCENTES
# ============================================================
class HorasDocente(models.Model):
    ESTADOS = [
        ("pendente", "Pendente"),
        ("validada", "Validada"),
        ("paga", "Paga"),
    ]
    aula = models.OneToOneField(Aula, on_delete=models.CASCADE)
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT)
    data = models.DateField()
    horas = models.DecimalField(max_digits=5, decimal_places=2)
    valor_hora = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendente")
 
    class Meta:
        verbose_name = "Horas do Docente"
        verbose_name_plural = "Horas dos Docentes"
 
    def __str__(self):
        return f"{self.docente.nome} - {self.horas}h = {self.valor_total} MT"
 
 
# ============================================================
# FOLHA DE PAGAMENTO
# ============================================================
class FolhaPagamento(models.Model):
    ESTADOS = [
        ("rascunho", "Rascunho"),
        ("validada", "Validada"),
        ("paga", "Paga"),
    ]
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT)
    mes = models.IntegerField()
    ano = models.IntegerField()
    total_horas = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="rascunho")
    data_geracao = models.DateTimeField(auto_now_add=True)
    data_validacao = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        unique_together = ("docente", "mes", "ano")
        verbose_name = "Folha de Pagamento"
        verbose_name_plural = "Folhas de Pagamento"
 
    def __str__(self):
        return f"{self.docente.nome} - {self.mes}/{self.ano}"
 
 
# ============================================================
# AUDITORIA
# ============================================================
class Auditoria(models.Model):
    utilizador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    entidade = models.CharField(max_length=100)
    entidade_id = models.IntegerField()
    operacao = models.CharField(max_length=50)
    data_hora = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    localizacao = models.CharField(max_length=200, blank=True)
    detalhes = models.TextField(blank=True)
 
    class Meta:
        verbose_name = "Auditoria"
        verbose_name_plural = "Auditorias"
 
    def __str__(self):
        return f"{self.utilizador} - {self.operacao} em {self.entidade}"
 
 
# ============================================================
# PEDIDO DE REVISÃO (aula bloqueada)
# ============================================================
class PedidoRevisao(models.Model):
    ESTADOS = [
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("rejeitado", "Rejeitado"),
    ]
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name="pedidos_revisao")
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT)
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendente")
    data_pedido = models.DateTimeField(auto_now_add=True)
    decidido_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="revisoes_decididas"
    )
    data_decisao = models.DateTimeField(null=True, blank=True)
    observacao = models.TextField(blank=True, help_text="Resposta da coordenação")
 
    class Meta:
        verbose_name = "Pedido de Revisão"
        verbose_name_plural = "Pedidos de Revisão"
 
    def __str__(self):
        return f"Revisão {self.aula} - {self.estado}"
 



