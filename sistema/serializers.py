from rest_framework import serializers
from .models import (
    CategoriaDocente, Docente, Curso, UC, Turma, Sala,
    Estudante, Inscricao, Horario, Aula, ValidacaoAula,
    Presenca, HorasDocente, FolhaPagamento, Auditoria
)


class CategoriaDocenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaDocente
        fields = "__all__"


class DocenteSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source="categoria.designacao", read_only=True)
    valor_hora = serializers.DecimalField(source="categoria.valor_hora", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Docente
        fields = "__all__"


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = "__all__"


class UCSerializer(serializers.ModelSerializer):
    class Meta:
        model = UC
        fields = "__all__"


class TurmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turma
        fields = "__all__"


class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = "__all__"


class EstudanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estudante
        fields = "__all__"


class InscricaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscricao
        fields = "__all__"


class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = "__all__"


class AulaSerializer(serializers.ModelSerializer):
    turma_codigo = serializers.CharField(source="turma.codigo", read_only=True)
    docente_nome = serializers.CharField(source="docente.nome", read_only=True)
    sala_codigo = serializers.CharField(source="sala.codigo", read_only=True)
    uc_nome = serializers.CharField(source="uc.nome", read_only=True)

    class Meta:
        model = Aula
        fields = "__all__"


class ValidacaoAulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidacaoAula
        fields = "__all__"


class PresencaSerializer(serializers.ModelSerializer):
    estudante_nome = serializers.CharField(source="estudante.nome", read_only=True)

    class Meta:
        model = Presenca
        fields = "__all__"


class HorasDocenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorasDocente
        fields = "__all__"


class FolhaPagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolhaPagamento
        fields = "__all__"


class AuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auditoria
        fields = "__all__"