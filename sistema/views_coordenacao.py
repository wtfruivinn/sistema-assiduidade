from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .auditoria import registar_auditoria
from .models import Aula, HorasDocente, PedidoRevisao, ValidacaoAula

# Grupos (além do superuser) que podem usar o painel da Coordenação
GRUPOS_COORDENACAO = ("Coordenacao", "RH")


# ============================================================
# PERMISSÕES
# ============================================================

def e_coordenacao(user):
    """True para o superuser e para quem está nos grupos Coordenacao ou RH."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=GRUPOS_COORDENACAO).exists()


def coordenacao_required(view):
    @login_required(login_url="login")
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not e_coordenacao(request.user):
            messages.warning(request, "Não tem permissão para aceder à área da Coordenação.")
            return redirect("painel")
        return view(request, *args, **kwargs)
    return _wrapped


# ============================================================
# PAINEL INICIAL DA COORDENAÇÃO
# ============================================================

@coordenacao_required
def coordenacao_painel(request):
    hoje = timezone.localdate()

    pendentes = (
        PedidoRevisao.objects.filter(estado="pendente")
        .select_related("docente", "aula", "aula__uc", "aula__turma", "aula__sala")
        .order_by("data_pedido")
    )
    decididos = (
        PedidoRevisao.objects.exclude(estado="pendente")
        .select_related("docente", "aula", "aula__uc", "decidido_por")
        .order_by("-data_decisao")[:10]
    )

    context = {
        "pedidos_pendentes": pendentes,
        "pedidos_decididos": decididos,
        "n_pedidos_pendentes": pendentes.count(),
        "n_aulas_bloqueadas": Aula.objects.filter(estado="bloqueada").count(),
        "n_horas_pendentes": HorasDocente.objects.filter(estado="pendente").count(),
        "n_aulas_hoje": Aula.objects.filter(data=hoje).count(),
    }
    return render(request, "sistema/coordenacao_painel.html", context)


# ============================================================
# DECIDIR UM PEDIDO DE REVISÃO (aprovar / rejeitar)
# ============================================================

@coordenacao_required
@require_POST
def coordenacao_decidir_pedido(request, pedido_id):
    pedido = get_object_or_404(PedidoRevisao, id=pedido_id)
    acao = request.POST.get("acao")
    observacao = request.POST.get("observacao", "").strip()

    if pedido.estado != "pendente":
        messages.warning(request, "Este pedido já tinha sido decidido.")
        return redirect("coordenacao")

    aula = pedido.aula

    if acao == "aprovar":
        with transaction.atomic():
            pedido.estado = "aprovado"
            pedido.decidido_por = request.user
            pedido.data_decisao = timezone.now()
            pedido.observacao = observacao
            pedido.save()

            # Validação manual feita pela coordenação
            ValidacaoAula.objects.create(
                aula=aula,
                docente=aula.docente,
                sala_validada=True,
                recinto_validado=True,
                horario_validado=True,
                qr_validado=False,
                resultado="autorizado",
            )
            if aula.estado == "bloqueada":
                aula.estado = "em_curso"
                aula.save()

        registar_auditoria(
            request, "PedidoRevisao", pedido.id, "aprovar_revisao",
            detalhes=f"Aula {aula.id} desbloqueada. Obs: {observacao}",
        )
        messages.success(
            request,
            f"Pedido aprovado. A aula de {aula.uc.nome} ({aula.turma.codigo}) voltou a 'Em curso'.",
        )

    elif acao == "rejeitar":
        if len(observacao) < 5:
            messages.warning(request, "Para rejeitar, escreva o motivo (mínimo 5 caracteres).")
            return redirect("coordenacao")

        pedido.estado = "rejeitado"
        pedido.decidido_por = request.user
        pedido.data_decisao = timezone.now()
        pedido.observacao = observacao
        pedido.save()

        registar_auditoria(
            request, "PedidoRevisao", pedido.id, "rejeitar_revisao",
            detalhes=f"Aula {aula.id} mantém-se bloqueada. Obs: {observacao}",
        )
        messages.success(request, "Pedido rejeitado. O docente vai ver o motivo.")

    else:
        messages.warning(request, "Ação inválida.")

    return redirect("coordenacao")
