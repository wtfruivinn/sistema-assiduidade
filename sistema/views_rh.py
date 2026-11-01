from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from .auditoria import registar_auditoria
from .models import Docente, HorasDocente, FolhaPagamento
from .views_coordenacao import e_coordenacao

def rh_required(view):
    @login_required(login_url="login")
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        # Apenas superuser ou grupo "RH"
        if not request.user.is_superuser and not request.user.groups.filter(name="RH").exists():
            messages.warning(request, "Não tem permissão para aceder à área de RH.")
            return redirect("painel")
        return view(request, *args, **kwargs)
    return _wrapped

@rh_required
def rh_painel(request):
    hoje = timezone.localdate()
    horas_pendentes = HorasDocente.objects.filter(estado="pendente").select_related("docente", "aula")
    folhas = FolhaPagamento.objects.all().order_by("-ano", "-mes", "docente__nome")
    
    context = {
        "horas_pendentes": horas_pendentes,
        "folhas": folhas,
        "total_horas_pendentes": horas_pendentes.aggregate(Sum("horas"))["horas__sum"] or 0,
        "total_valor_pendente": horas_pendentes.aggregate(Sum("valor_total"))["valor_total__sum"] or 0,
    }
    return render(request, "sistema/rh_painel.html", context)

@rh_required
def rh_aprovar_horas(request, hora_id):
    from .models import HorasDocente
    hora = HorasDocente.objects.get(id=hora_id)
    if hora.estado == "pendente":
        hora.estado = "validada"
        hora.save()
        registar_auditoria(request, "HorasDocente", hora.id, "rh_aprovar_horas")
        messages.success(request, "Horas aprovadas.")
    return redirect("rh_painel")

@rh_required
def rh_gerar_folha(request):
    hoje = timezone.localdate()
    mes = int(request.POST.get("mes", hoje.month))
    ano = int(request.POST.get("ano", hoje.year))
    
    docentes = Docente.objects.all()
    geradas = 0
    for docente in docentes:
        horas = HorasDocente.objects.filter(docente=docente, estado="validada", data__month=mes, data__year=ano)
        totais = horas.aggregate(h=Sum("horas"), v=Sum("valor_total"))
        if totais["h"]:
            folha, _ = FolhaPagamento.objects.update_or_create(
                docente=docente, mes=mes, ano=ano,
                defaults={
                    "total_horas": totais["h"] or 0,
                    "valor_total": totais["v"] or 0,
                    "estado": "rascunho",
                }
            )
            geradas += 1
    messages.success(request, f"{geradas} folhas geradas para {mes:02d}/{ano}.")
    return redirect("rh_painel")

@rh_required
def rh_validar_folha(request, folha_id):
    from .models import FolhaPagamento
    folha = FolhaPagamento.objects.get(id=folha_id)
    if folha.estado == "rascunho":
        folha.estado = "validada"
        folha.data_validacao = timezone.now()
        folha.save()
        messages.success(request, "Folha validada.")
    return redirect("rh_painel")

@rh_required
def rh_pagar_folha(request, folha_id):
    from .models import FolhaPagamento, HorasDocente
    folha = FolhaPagamento.objects.get(id=folha_id)
    if folha.estado == "validada":
        folha.estado = "paga"
        folha.save()
        HorasDocente.objects.filter(
            docente=folha.docente, estado="validada",
            data__month=folha.mes, data__year=folha.ano
        ).update(estado="paga")
        messages.success(request, "Folha marcada como paga.")
    return redirect("rh_painel")

@rh_required
def rh_exportar_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Folha de Pagamento"
    ws.append(["Docente", "Mês/Ano", "Horas", "Valor Total (MT)", "Estado"])
    for f in FolhaPagamento.objects.all().order_by("-ano", "-mes", "docente__nome"):
        ws.append([f.docente.nome, f"{f.mes:02d}/{f.ano}", float(f.total_horas), float(f.valor_total), f.get_estado_display()])
    
    resposta = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resposta["Content-Disposition"] = 'attachment; filename="folha_pagamento.xlsx"'
    wb.save(resposta)
    return resposta
