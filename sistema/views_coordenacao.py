from functools import wraps
from datetime import date, time, timedelta, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .auditoria import registar_auditoria
from .models import (
    Aula, Docente, Horario, HorasDocente, PedidoHorario, PedidoRevisao, 
    Sala, Turma, UC, ValidacaoAula
)

GRUPOS_COORDENACAO = ("Coordenacao", "RH")


def e_coordenacao(user):
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
# PAINEL INICIAL
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
    
    horas_pendentes = (
        HorasDocente.objects.filter(estado="pendente")
        .select_related("docente", "aula", "aula__uc")
        .order_by("data")
    )

    pedidos_horarios_pendentes = (
        PedidoHorario.objects.filter(estado="pendente")
        .select_related("docente", "turma", "sala")
        .order_by("data_pedido")
    )

    context = {
        "pedidos_pendentes": pendentes,
        "pedidos_decididos": decididos,
        "horas_pendentes": horas_pendentes,
        "pedidos_horarios_pendentes": pedidos_horarios_pendentes,
        "n_pedidos_pendentes": pendentes.count(),
        "n_aulas_bloqueadas": Aula.objects.filter(estado="bloqueada").count(),
        "n_horas_pendentes": horas_pendentes.count(),
        "n_aulas_hoje": Aula.objects.filter(data=hoje).count(),
    }
    return render(request, "sistema/coordenacao_painel.html", context)


# ============================================================
# DECIDIR PEDIDO DE REVISÃO (aula bloqueada)
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

            ValidacaoAula.objects.create(
                aula=aula, docente=aula.docente,
                sala_validada=True, recinto_validado=True,
                horario_validado=True, qr_validado=False,
                resultado="autorizado",
            )
            if aula.estado == "bloqueada":
                aula.estado = "em_curso"
                aula.save()

        registar_auditoria(request, "PedidoRevisao", pedido.id, "aprovar_revisao",
                           detalhes=f"Aula {aula.id} desbloqueada. Obs: {observacao}")
        messages.success(request, f"Pedido aprovado. A aula de {aula.uc.nome} voltou a 'Em curso'.")

    elif acao == "rejeitar":
        if len(observacao) < 5:
            messages.warning(request, "Para rejeitar, escreva o motivo (mínimo 5 caracteres).")
            return redirect("coordenacao")

        pedido.estado = "rejeitado"
        pedido.decidido_por = request.user
        pedido.data_decisao = timezone.now()
        pedido.observacao = observacao
        pedido.save()

        registar_auditoria(request, "PedidoRevisao", pedido.id, "rejeitar_revisao",
                           detalhes=f"Aula {aula.id} mantém-se bloqueada. Obs: {observacao}")
        messages.success(request, "Pedido rejeitado. O docente vai ver o motivo.")

    else:
        messages.warning(request, "Ação inválida.")

    return redirect("coordenacao")


# ============================================================
# APROVAR HORAS PENDENTES
# ============================================================
@coordenacao_required
@require_POST
def coordenacao_aprovar_horas(request, hora_id):
    """Aprova um registo de horas pendente."""
    hora = get_object_or_404(HorasDocente, id=hora_id)
    
    if hora.estado != "pendente":
        messages.warning(request, "Estas horas já foram processadas.")
        return redirect("coordenacao")
    
    hora.estado = "validada"
    hora.save()
    
    registar_auditoria(request, "HorasDocente", hora.id, "aprovar_horas",
                       detalhes=f"Aprovadas {hora.horas}h para {hora.docente.nome}.")
    messages.success(request, f"Horas de {hora.docente.nome} aprovadas com sucesso.")
    return redirect("coordenacao")


# ============================================================
# APROVAR/REJEITAR PEDIDO DE HORÁRIO (agora cria também a Aula)
# ============================================================
@coordenacao_required
@require_POST
def coordenacao_aprovar_horario(request, pedido_id):
    pedido = get_object_or_404(PedidoHorario, id=pedido_id)
    if pedido.estado != "pendente":
        messages.warning(request, "Este pedido já foi decidido.")
        return redirect("coordenacao")

    acao = request.POST.get("acao")
    obs = request.POST.get("observacao", "").strip()

    if acao == "aprovar":
        try:
            with transaction.atomic():
                # 1. Cria o horário oficial
                Horario.objects.create(
                    turma=pedido.turma, 
                    docente=pedido.docente, 
                    sala=pedido.sala,
                    dia_semana=pedido.dia_semana, 
                    hora_inicio=pedido.hora_inicio,
                    hora_fim=pedido.hora_fim, 
                    ano_letivo=pedido.ano_letivo,
                    semestre=pedido.semestre
                )
                
                # 2. Cria a Aula para a data de início (ou hoje, se não houver)
                data_inicio = pedido.data_inicio or timezone.localdate()
                dias_map = {"SEG": 0, "TER": 1, "QUA": 2, "QUI": 3, "SEX": 4, "SAB": 5}
                delta = (dias_map[pedido.dia_semana] - data_inicio.weekday()) % 7
                data_aula = data_inicio + timedelta(days=delta)
                
                Aula.objects.create(
                    turma=pedido.turma,
                    docente=pedido.docente,
                    uc=pedido.turma.uc,
                    sala=pedido.sala,
                    data=data_aula,
                    hora_inicio=pedido.hora_inicio,
                    hora_fim=pedido.hora_fim,
                    estado="agendada",
                )
                
                # 3. Atualiza o estado do pedido
                pedido.estado = "aprovado"
                pedido.decidido_por = request.user
                pedido.data_decisao = timezone.now()
                pedido.observacao = obs
                pedido.save()

            registar_auditoria(request, "PedidoHorario", pedido.id, "aprovar_horario", detalhes=f"Horário e Aula criados para {pedido.docente.nome}.")
            messages.success(request, f"Horário e Aula de {pedido.docente.nome} aprovados e criados com sucesso.")
        except Exception as e:
            messages.error(request, f"Erro ao criar o horário/aula: {str(e)}")

    elif acao == "rejeitar":
        if len(obs) < 5:
            messages.warning(request, "Escreva o motivo da rejeição (mínimo 5 caracteres).")
            return redirect("coordenacao")
        pedido.estado = "rejeitado"
        pedido.decidido_por = request.user
        pedido.data_decisao = timezone.now()
        pedido.observacao = obs
        pedido.save()

        registar_auditoria(request, "PedidoHorario", pedido.id, "rejeitar_horario", detalhes=f"Motivo: {obs}")
        messages.success(request, "Pedido de horário rejeitado.")

    return redirect("coordenacao")


# ============================================================
# GERAR AULAS DA SEMANA (a partir dos Horários aprovados)
# ============================================================
@coordenacao_required
@require_POST
def coordenacao_gerar_aulas(request):
    """Gera as aulas da semana atual a partir dos Horarios, sem duplicar."""
    horarios = Horario.objects.select_related("turma", "turma__uc", "docente", "sala")
    
    if not horarios.exists():
        messages.warning(request, "Não há horários criados para gerar aulas.")
        return redirect("coordenacao")
    
    hoje = timezone.localdate()
    segunda = hoje - timedelta(days=hoje.weekday())
    dias_map = {"SEG": 0, "TER": 1, "QUA": 2, "QUI": 3, "SEX": 4, "SAB": 5}
    
    criadas = 0
    for h in horarios:
        delta_dias = dias_map.get(h.dia_semana)
        if delta_dias is None:
            continue
        data_aula = segunda + timedelta(days=delta_dias)
        
        ja_existe = Aula.objects.filter(
            turma=h.turma, docente=h.docente, uc=h.turma.uc,
            sala=h.sala, data=data_aula, hora_inicio=h.hora_inicio
        ).exists()
        
        if not ja_existe:
            Aula.objects.create(
                turma=h.turma,
                docente=h.docente,
                uc=h.turma.uc,
                sala=h.sala,
                data=data_aula,
                hora_inicio=h.hora_inicio,
                hora_fim=h.hora_fim,
                estado="agendada",
            )
            criadas += 1
            print(f"Criada aula: {h.turma.codigo} - {h.docente.nome} - {data_aula}")

    registar_auditoria(request, "Aula", 0, "gerar_aulas_semana",
                       detalhes=f"Criadas {criadas} aulas a partir dos horários.")
    messages.success(request, f"Foram criadas {criadas} aulas para a semana atual.")
    return redirect("coordenacao")


# ============================================================
# CRIAR HORÁRIO E AULA (Coordenação) - NOVA FUNÇÃO
# ============================================================
@coordenacao_required
def coordenacao_criar_horario(request):
    """Formulário para a coordenação criar um horário e a aula correspondente."""
    if request.method == "POST":
        turma_id = request.POST.get("turma")
        docente_id = request.POST.get("docente")
        sala_id = request.POST.get("sala")
        dia = request.POST.get("dia_semana")
        inicio = request.POST.get("hora_inicio")
        fim = request.POST.get("hora_fim")
        data_inicio = request.POST.get("data_inicio")

        if not all([turma_id, docente_id, sala_id, dia, inicio, fim, data_inicio]):
            messages.error(request, "Preencha todos os campos.")
        else:
            try:
                with transaction.atomic():
                    turma = Turma.objects.get(id=turma_id)
                    docente = Docente.objects.get(id=docente_id)
                    sala = Sala.objects.get(id=sala_id)

                    # 1. Cria o Horário
                    Horario.objects.create(
                        turma=turma, docente=docente, sala=sala,
                        dia_semana=dia, hora_inicio=inicio, hora_fim=fim,
                        ano_letivo="2025/2026", semestre="1º"
                    )

                    # 2. Calcula a data da Aula
                    data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d").date()
                    dias_map = {"SEG": 0, "TER": 1, "QUA": 2, "QUI": 3, "SEX": 4, "SAB": 5}
                    delta = (dias_map[dia] - data_inicio_obj.weekday()) % 7
                    data_aula = data_inicio_obj + timedelta(days=delta)

                    # 3. Cria a Aula
                    Aula.objects.create(
                        turma=turma, docente=docente, uc=turma.uc, sala=sala,
                        data=data_aula, hora_inicio=inicio, hora_fim=fim,
                        estado="agendada"
                    )

                    registar_auditoria(request, "Horario", 0, "criar_horario_coordenacao",
                                       detalhes=f"Horário e Aula criados: {turma.codigo} - {docente.nome}")
                    messages.success(request, f"Horário e Aula criados para {docente.nome} na turma {turma.codigo}.")
                    return redirect("coordenacao")
            except (Turma.DoesNotExist, Docente.DoesNotExist, Sala.DoesNotExist):
                messages.error(request, "Turma, docente ou sala inválida.")
            except Exception as e:
                messages.error(request, f"Erro ao criar: {str(e)}")

    # Dados para os dropdowns
    turmas = Turma.objects.filter(estado=True).select_related("uc", "uc__curso")
    docentes = Docente.objects.filter(estado=True).order_by("nome")
    salas = Sala.objects.filter(estado=True).order_by("codigo")

    return render(request, "sistema/coordenacao_criar_horario.html", {
        "turmas": turmas,
        "docentes": docentes,
        "salas": salas,
    })