from django.db import transaction
from django.db.models import Sum
from django.http import QueryDict
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
 
from . import views
from .auditoria import registar_auditoria
from .models import Aula, Docente, FolhaPagamento, HorasDocente, Presenca, Sala
from .serializers import (
    AulaSerializer, DocenteSerializer, HorasDocenteSerializer,
    PresencaSerializer, SalaSerializer,
)
 
 
# ============================================================
# PERFIS E PERMISSÕES
# ============================================================
 
def e_rh(user):
    """Superuser ou membro do grupo 'RH'."""
    return user.is_superuser or user.groups.filter(name="RH").exists()
 
 
def e_gestor(user):
    """Superuser ou membro dos grupos 'RH' ou 'Coordenacao'."""
    return user.is_superuser or user.groups.filter(name__in=["RH", "Coordenacao"]).exists()
 
 
class IsRH(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and e_rh(request.user))
 
 
class IsGestor(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and e_gestor(request.user))
 
 
def _ler_mes_ano(request):
    """Lê ?mes= e ?ano= (ou dados do POST). Por defeito, o mês atual."""
    hoje = timezone.localdate()
    origem = request.data if request.method == "POST" else request.query_params
    mes = int(origem.get("mes") or hoje.month)
    ano = int(origem.get("ano") or hoje.year)
    if not 1 <= mes <= 12:
        raise ValueError("mes")
    return mes, ano
 
 
# ============================================================
# DOCENTES
# ============================================================
 
class DocenteViewSet(viewsets.ReadOnlyModelViewSet):
    """Um docente só vê o seu próprio registo. RH/Coordenação veem todos."""
    serializer_class = DocenteSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        if e_gestor(self.request.user):
            return Docente.objects.all()
        return Docente.objects.filter(user=self.request.user)
 
    @action(detail=True, methods=["get"])
    def aulas(self, request, pk=None):
        docente = self.get_object()
        aulas = Aula.objects.filter(docente=docente).order_by("-data", "-hora_inicio")
        return Response(AulaSerializer(aulas, many=True).data)
 
    @action(detail=True, methods=["get"])
    def horas(self, request, pk=None):
        docente = self.get_object()
        horas = HorasDocente.objects.filter(docente=docente).order_by("-data")
        totais = horas.aggregate(h=Sum("horas"), v=Sum("valor_total"))
        return Response({
            "docente": docente.nome,
            "total_horas": float(totais["h"] or 0),
            "total_valor": float(totais["v"] or 0),
            "detalhes": HorasDocenteSerializer(horas, many=True).data,
        })
 
    @action(detail=True, methods=["get"])
    def pagamento(self, request, pk=None):
        """Pagamento do mês (?mes=10&ano=2026). Só as horas validadas entram (RN09)."""
        docente = self.get_object()
        try:
            mes, ano = _ler_mes_ano(request)
        except ValueError:
            return Response({"erro": "Parâmetros mes/ano inválidos."}, status=400)
 
        base = HorasDocente.objects.filter(docente=docente, data__month=mes, data__year=ano)
 
        def soma(estado):
            t = base.filter(estado=estado).aggregate(h=Sum("horas"), v=Sum("valor_total"))
            return {"horas": float(t["h"] or 0), "valor": float(t["v"] or 0)}
 
        folha = FolhaPagamento.objects.filter(docente=docente, mes=mes, ano=ano).first()
        return Response({
            "docente": docente.nome,
            "mes": mes,
            "ano": ano,
            "a_pagar_validadas": soma("validada"),
            "pendentes_aprovacao": soma("pendente"),
            "ja_pagas": soma("paga"),
            "folha": None if folha is None else {
                "id": folha.id,
                "estado": folha.estado,
                "total_horas": float(folha.total_horas),
                "valor_total": float(folha.valor_total),
            },
        })
 
 
# ============================================================
# AULAS — as ações usam EXATAMENTE as mesmas regras da interface web
# (dono da aula, janela de horário, 3 tentativas, recinto/sala, mínimo de
# horas, auditoria...), porque delegam nas funções do views.py.
# ============================================================
 
class AulaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AulaSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        qs = Aula.objects.all().order_by("-data", "-hora_inicio")
        if e_gestor(self.request.user):
            return qs
        return qs.filter(docente__user=self.request.user)
 
    def _delegar(self, request, funcao):
        aula = self.get_object()  # 404 se a aula não for visível a este utilizador
        pedido = request._request
        pedido.user = request.user
        dados = QueryDict(mutable=True)
        for chave, valor in request.data.items():
            dados[chave] = str(valor)
        pedido._post = dados
        return funcao(pedido, aula.id)
 
    @action(detail=True, methods=["post"])
    def iniciar(self, request, pk=None):
        return self._delegar(request, views.api_iniciar_aula)
 
    @action(detail=True, methods=["post"], url_path="validar-local")
    def validar_local(self, request, pk=None):
        return self._delegar(request, views.api_validar_local)
 
    @action(detail=True, methods=["post"])
    def encerrar(self, request, pk=None):
        return self._delegar(request, views.api_encerrar_aula)
 
 
# ============================================================
# SALAS (contêm o código QR: só RH/Coordenação) e PRESENÇAS
# ============================================================
 
class SalaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    permission_classes = [IsGestor]
 
 
class PresencaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PresencaSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        qs = Presenca.objects.all()
        if e_gestor(self.request.user):
            return qs
        return qs.filter(aula__docente__user=self.request.user)
 
 
# ============================================================
# RH — FOLHA DE PAGAMENTO
# GET  /api/rh/folha-pagamento
# POST /api/rh/folha-pagamento/gerar   (corpo: mes, ano — opcionais)
# ============================================================
 
def _folha_dict(f):
    return {
        "id": f.id,
        "numero_docente": f.docente.numero_docente,
        "docente": f.docente.nome,
        "mes": f.mes,
        "ano": f.ano,
        "total_horas": float(f.total_horas),
        "valor_total": float(f.valor_total),
        "estado": f.estado,
    }
 
 
class FolhaPagamentoListView(APIView):
    permission_classes = [IsRH]
 
    def get(self, request):
        folhas = FolhaPagamento.objects.select_related("docente").order_by(
            "-ano", "-mes", "docente__nome"
        )
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")
        if mes and mes.isdigit():
            folhas = folhas.filter(mes=int(mes))
        if ano and ano.isdigit():
            folhas = folhas.filter(ano=int(ano))
        return Response([_folha_dict(f) for f in folhas])
 
 
class FolhaPagamentoGerarView(APIView):
    permission_classes = [IsRH]
 
    def post(self, request):
        try:
            mes, ano = _ler_mes_ano(request)
        except ValueError:
            return Response({"erro": "Parâmetros mes/ano inválidos."}, status=400)
 
        geradas = 0
        ignoradas = 0
        with transaction.atomic():
            for docente in Docente.objects.filter(estado=True):
                existente = FolhaPagamento.objects.filter(docente=docente, mes=mes, ano=ano).first()
                # Folha já validada ou paga não se mexe
                if existente and existente.estado != "rascunho":
                    ignoradas += 1
                    continue
 
                totais = HorasDocente.objects.filter(
                    docente=docente, estado="validada", data__month=mes, data__year=ano
                ).aggregate(h=Sum("horas"), v=Sum("valor_total"))
 
                folha, _ = FolhaPagamento.objects.update_or_create(
                    docente=docente, mes=mes, ano=ano,
                    defaults={
                        "total_horas": totais["h"] or 0,
                        "valor_total": totais["v"] or 0,
                        "estado": "rascunho",
                    },
                )
                registar_auditoria(
                    request, "FolhaPagamento", folha.id, "gerar_folha",
                    detalhes=(f"API. Docente {docente.numero_docente}. Período {mes:02d}/{ano}. "
                              f"Horas: {folha.total_horas}. Valor: {folha.valor_total} MT."),
                )
                geradas += 1
 
        return Response({
            "mensagem": f"{geradas} folha(s) gerada(s) para {mes:02d}/{ano}.",
            "geradas": geradas,
            "ignoradas_ja_validadas_ou_pagas": ignoradas,
        })
 
