from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from geopy.distance import geodesic
from django.db import transaction

# Importação de todos os modelos necessários
from .models import (
    Aula, Docente, Presenca, ValidacaoAula, HorasDocente, Inscricao,
    PedidoRevisao, PedidoHorario, Horario, Turma, Sala
)
from .auditoria import registar_auditoria
from .views_coordenacao import e_coordenacao

# ============================================================
# CONFIGURAÇÕES DO SISTEMA
# ============================================================
RAIO_GPS_METROS = 100
MAX_TENTATIVAS_VALIDACAO = 3
VALIDAR_JANELA_HORARIO = True
JANELA_ANTES_MIN = 15
PERCENTAGEM_MINIMA = Decimal("0.50")
ESTADOS_PRESENCA = {"presente", "falta", "falta_justificada"}


# ============================================================
# FUNÇÕES AUXILIARES — PERMISSÕES
# ============================================================
def _nao_e_dono(request, aula):
    if request.user.is_superuser:
        return False
    return aula.docente.user_id != request.user.id

def _erro_dono(request, aula):
    registar_auditoria(
        request, "Aula", aula.id, "acesso_negado",
        detalhes="Tentou mexer numa aula que não é do seu utilizador.",
    )
    return JsonResponse({"erro": "Esta aula não pertence ao seu utilizador."}, status=403)


# ============================================================
# AUTENTICAÇÃO
# ============================================================
def pagina_login(request):
    if request.user.is_authenticated:
        return redirect("painel")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            registar_auditoria(request, "Utilizador", user.id, "login")
            messages.success(request, f"Bem-vindo, {user.username}!")
            return redirect("painel")
        else:
            registar_auditoria(
                request, "Utilizador", 0, "login_falhado",
                detalhes=f"Utilizador tentado: {username}",
            )
            return render(request, "sistema/login.html", {"erro": "Utilizador ou palavra-passe incorretos."})
    return render(request, "sistema/login.html")


def pagina_logout(request):
    if request.user.is_authenticated:
        registar_auditoria(request, "Utilizador", request.user.id, "logout")
    logout(request)
    messages.info(request, "Sessão terminada com sucesso.")
    return redirect("login")


def pagina_inicial(request):
    if request.user.is_authenticated:
        return redirect("painel")
    return redirect("login")


# ============================================================
# PAINEL DO DOCENTE
# ============================================================
@login_required(login_url="login")
def painel_docente(request):
    if e_coordenacao(request.user):
        return redirect("coordenacao")

    try:
        docente = Docente.objects.get(user=request.user)
    except Docente.DoesNotExist:
        docente = None

    if request.user.is_superuser:
        aulas = Aula.objects.all().order_by("-data", "-hora_inicio")
    elif docente:
        aulas = Aula.objects.filter(docente=docente).order_by("-data", "-hora_inicio")
    else:
        aulas = Aula.objects.none()

    context = {
        "docente": docente,
        "aulas": aulas,
        "total_aulas": aulas.count(),
        "aulas_validadas": aulas.filter(estado="validada").count(),
        "aulas_agendadas": aulas.filter(estado="agendada").count(),
    }
    return render(request, "sistema/painel.html", context)


@login_required(login_url="login")
def detalhe_aula(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)
    if _nao_e_dono(request, aula):
        registar_auditoria(
            request, "Aula", aula.id, "acesso_negado",
            detalhes="Tentou abrir o detalhe de uma aula que não é do seu utilizador.",
        )
        messages.error(request, "Esta aula não pertence ao seu utilizador.")
        return redirect("painel")

    inscricoes = Inscricao.objects.filter(turma=aula.turma)
    estudantes = [i.estudante for i in inscricoes]
    presencas = Presenca.objects.filter(aula=aula)
    validacao = ValidacaoAula.objects.filter(aula=aula).order_by("-data_hora").first()
    context = {
        "aula": aula,
        "estudantes": estudantes,
        "presencas": presencas,
        "validacao": validacao,
    }
    return render(request, "sistema/aula_detalhe.html", context)


# ============================================================
# PROPOR HORÁRIO (Docente) — com data_inicio
# ============================================================
@login_required(login_url="login")
def propor_horario(request):
    """O docente propõe um horário à coordenação."""
    try:
        docente = Docente.objects.get(user=request.user)
    except Docente.DoesNotExist:
        messages.error(request, "Apenas docentes podem propor horários.")
        return redirect("painel")

    if request.method == "POST":
        turma_id = request.POST.get("turma")
        sala_id = request.POST.get("sala")
        dia = request.POST.get("dia_semana")
        inicio = request.POST.get("hora_inicio")
        fim = request.POST.get("hora_fim")
        data_inicio = request.POST.get("data_inicio")

        if not all([turma_id, sala_id, dia, inicio, fim, data_inicio]):
            messages.error(request, "Preencha todos os campos.")
        else:
            try:
                turma = Turma.objects.get(id=turma_id)
                sala = Sala.objects.get(id=sala_id)
                
                existe = PedidoHorario.objects.filter(
                    docente=docente, turma=turma, dia_semana=dia, 
                    hora_inicio=inicio, estado="pendente"
                ).exists()
                
                if existe:
                    messages.warning(request, "Já tem um pedido pendente para este horário.")
                else:
                    PedidoHorario.objects.create(
                        docente=docente, turma=turma, sala=sala,
                        dia_semana=dia, hora_inicio=inicio, hora_fim=fim,
                        data_inicio=data_inicio
                    )
                    messages.success(request, "Pedido de horário enviado para a coordenação.")
                    return redirect("painel")
            except (Turma.DoesNotExist, Sala.DoesNotExist):
                messages.error(request, "Turma ou sala inválida.")

    # Filtra apenas turmas de cursos de Informática
    turmas = Turma.objects.filter(
        estado=True,
        uc__curso__nome__icontains="Informática"
    ).distinct()
    
    salas = Sala.objects.filter(estado=True)
    return render(request, "sistema/propor_horario.html", {
        "turmas": turmas, "salas": salas, "docente": docente
    })


# ============================================================
# API AJAX — INICIAR AULA
# ============================================================
@login_required(login_url="login")
@require_POST
def api_iniciar_aula(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)
    if _nao_e_dono(request, aula):
        return _erro_dono(request, aula)

    if aula.estado == "em_curso":
        return JsonResponse({
            "sucesso": True,
            "mensagem": "A aula já estava em curso.",
            "estado": aula.estado,
        })

    if aula.estado != "agendada":
        return JsonResponse({"erro": "A aula não pode ser iniciada neste estado."}, status=400)

    if VALIDAR_JANELA_HORARIO:
        agora = datetime.now()
        inicio_prev = datetime.combine(aula.data, aula.hora_inicio)
        fim_prev = datetime.combine(aula.data, aula.hora_fim)
        abertura = inicio_prev - timedelta(minutes=JANELA_ANTES_MIN)
        if agora < abertura:
            return JsonResponse({
                "erro": f"Ainda é cedo. Pode iniciar a partir das {abertura.strftime('%H:%M')}."
            }, status=400)
        if agora > fim_prev:
            return JsonResponse({"erro": "O horário desta aula já terminou."}, status=400)

    aula.estado = "em_curso"
    aula.hora_inicio_real = datetime.now().time()
    aula.save()

    registar_auditoria(
        request, "Aula", aula.id, "iniciar_aula",
        detalhes=f"Estado: agendada -> em_curso. Hora de início real: "
                 f"{aula.hora_inicio_real.strftime('%H:%M:%S')}. Sala: {aula.sala.codigo}.",
    )

    return JsonResponse({
        "sucesso": True,
        "mensagem": "Aula iniciada. Valide a localização.",
        "estado": aula.estado,
    })


# ============================================================
# API AJAX — VALIDAR LOCALIZAÇÃO
# ============================================================
@login_required(login_url="login")
@require_POST
def api_validar_local(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)

    if _nao_e_dono(request, aula):
        return _erro_dono(request, aula)

    if aula.estado != "em_curso":
        return JsonResponse({"erro": "Inicie a aula antes de validar a localização."}, status=400)

    sala = aula.sala
    recinto = sala.recinto if (sala.recinto and sala.recinto.estado) else None

    latitude = request.POST.get("latitude")
    longitude = request.POST.get("longitude")
    qr_lido = request.POST.get("qr_code", "")
    wifi_ssid = request.POST.get("wifi_ssid", "")

    sala_validada = False
    recinto_validado = False
    qr_validado = False
    resultado = "bloqueado"
    mensagem = ""
    metodo = "nenhum"

    if qr_lido and qr_lido == sala.qr_code:
        metodo = "qr"
        qr_validado = True
        sala_validada = True
        recinto_validado = True
        resultado = "autorizado"
        mensagem = f"✅ QR Code validado. Bem-vindo à {sala.codigo}."

    elif wifi_ssid and wifi_ssid == sala.wifi_ssid:
        metodo = "wifi"
        sala_validada = True
        recinto_validado = True
        resultado = "autorizado"
        mensagem = f"✅ Rede Wi-Fi '{wifi_ssid}' corresponde à sala."

    elif latitude and longitude:
        metodo = "gps"
        if not (sala.latitude and sala.longitude):
            mensagem = "❌ A sala não tem coordenadas GPS configuradas. Contacte o administrador."
        else:
            try:
                ponto_docente = (float(latitude), float(longitude))
                ponto_sala = (float(sala.latitude), float(sala.longitude))
                dist_sala = geodesic(ponto_docente, ponto_sala).meters
                precisao = float(request.POST.get("precisao") or 0)

                dentro_recinto = True
                dist_recinto = None
                if recinto:
                    ponto_recinto = (float(recinto.latitude), float(recinto.longitude))
                    dist_recinto = geodesic(ponto_docente, ponto_recinto).meters
                    dentro_recinto = dist_recinto <= recinto.raio_metros

                if recinto and not dentro_recinto:
                    mensagem = (f"❌ Está fora do recinto ({recinto.nome}): a {dist_recinto:.0f}m "
                                f"do centro (limite: {recinto.raio_metros}m). "
                                f"Precisão do GPS: {precisao:.0f}m.")
                elif dist_sala <= RAIO_GPS_METROS:
                    recinto_validado = True
                    sala_validada = True
                    resultado = "autorizado"
                    mensagem = (f"✅ Localização validada. Distância à sala: {dist_sala:.0f}m "
                                f"(precisão do GPS: {precisao:.0f}m).")
                elif recinto:
                    recinto_validado = True
                    mensagem = (f"❌ Está no recinto, mas não na sala prevista ({sala.codigo}): "
                                f"a {dist_sala:.0f}m (limite: {RAIO_GPS_METROS}m). "
                                f"Precisão do GPS: {precisao:.0f}m. Dirija-se à sala e tente outra vez.")
                else:
                    mensagem = (f"❌ Está a {dist_sala:.0f}m da sala "
                                f"(limite: {RAIO_GPS_METROS}m). Precisão do GPS: {precisao:.0f}m. "
                                f"Aproxime-se e tente outra vez.")
            except (ValueError, TypeError):
                mensagem = "❌ Coordenadas GPS inválidas."
    else:
        mensagem = "❌ Nenhum método de validação foi detetado."

    ValidacaoAula.objects.create(
        aula=aula,
        docente=aula.docente,
        latitude=latitude or None,
        longitude=longitude or None,
        sala_validada=sala_validada,
        recinto_validado=recinto_validado,
        horario_validado=True,
        qr_validado=qr_validado,
        resultado=resultado,
    )

    localizacao = f"{latitude},{longitude}" if (latitude and longitude) else ""
    registar_auditoria(
        request, "Aula", aula.id, f"validar_local_{resultado}",
        localizacao=localizacao,
        detalhes=(f"Método: {metodo}. Sala: {sala.codigo}. "
                  f"Recinto validado: {recinto_validado}. Sala validada: {sala_validada}. "
                  f"{mensagem}"),
    )

    if resultado == "bloqueado":
        falhadas = ValidacaoAula.objects.filter(aula=aula, resultado="bloqueado").count()
        restantes = MAX_TENTATIVAS_VALIDACAO - falhadas

        if restantes <= 0:
            aula.estado = "bloqueada"
            aula.save()
            registar_auditoria(
                request, "Aula", aula.id, "aula_bloqueada",
                localizacao=localizacao,
                detalhes=f"Esgotou as {MAX_TENTATIVAS_VALIDACAO} tentativas de validação.",
            )
            return JsonResponse({
                "sucesso": False,
                "resultado": "bloqueado",
                "bloqueada": True,
                "mensagem": (f"{mensagem}\n🔒 AULA BLOQUEADA — esgotou as "
                             f"{MAX_TENTATIVAS_VALIDACAO} tentativas."),
            }, status=403)

        return JsonResponse({
            "sucesso": False,
            "resultado": "bloqueado",
            "bloqueada": False,
            "tentativas_restantes": restantes,
            "mensagem": f"{mensagem}\nTentativas restantes: {restantes}.",
        })

    return JsonResponse({
        "sucesso": True,
        "resultado": "autorizado",
        "mensagem": mensagem,
    })


# ============================================================
# API AJAX — REGISTAR PRESENÇAS
# ============================================================
@login_required(login_url="login")
@require_POST
def api_registar_presencas(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)

    if _nao_e_dono(request, aula):
        return _erro_dono(request, aula)

    if aula.estado != "em_curso":
        return JsonResponse({"erro": "Só pode registar presenças com a aula em curso."}, status=400)

    total = 0
    for key, valor in request.POST.items():
        if key.startswith("estudante_") and valor in ESTADOS_PRESENCA:
            eid = key.replace("estudante_", "")
            Presenca.objects.update_or_create(
                aula=aula, estudante_id=eid, defaults={"estado": valor}
            )
            total += 1

    registar_auditoria(
        request, "Aula", aula.id, "registar_presencas",
        detalhes=f"{total} presenças registadas.",
    )

    return JsonResponse({
        "sucesso": True,
        "mensagem": f"✅ {total} presenças registadas.",
        "total": total,
    })


# ============================================================
# API AJAX — ENCERRAR AULA
# ============================================================
@login_required(login_url="login")
@require_POST
def api_encerrar_aula(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)

    if _nao_e_dono(request, aula):
        return _erro_dono(request, aula)

    if aula.estado != "em_curso":
        return JsonResponse({"erro": "A aula não está em curso."}, status=400)

    if not ValidacaoAula.objects.filter(aula=aula, resultado="autorizado").exists():
        return JsonResponse({"erro": "Valide a localização antes de encerrar a aula."}, status=400)

    sumario = request.POST.get("sumario", "").strip()
    tema = request.POST.get("tema", "").strip()

    if not sumario or not tema:
        return JsonResponse({"erro": "Sumário e tema são obrigatórios."}, status=400)

    if not aula.presencas.exists():
        return JsonResponse({"erro": "Registe as presenças antes de encerrar."}, status=400)

    agora = datetime.now()
    inicio_prev = datetime.combine(aula.data, aula.hora_inicio)
    fim_prev = datetime.combine(aula.data, aula.hora_fim)

    segundos_previstos = (fim_prev - inicio_prev).total_seconds()
    if segundos_previstos <= 0:
        return JsonResponse({"erro": "Horário previsto da aula inválido. Contacte o administrador."}, status=400)

    if aula.hora_inicio_real:
        inicio_real = datetime.combine(aula.data, aula.hora_inicio_real)
    else:
        inicio_real = inicio_prev

    inicio_contado = max(inicio_real, inicio_prev)
    fim_contado = min(agora, fim_prev)
    segundos = max((fim_contado - inicio_contado).total_seconds(), 0)

    horas = Decimal(str(round(segundos / 3600, 2)))
    horas_previstas = Decimal(str(round(segundos_previstos / 3600, 2)))
    minimo = (horas_previstas * PERCENTAGEM_MINIMA).quantize(Decimal("0.01"))

    pendente = horas < minimo
    estado_horas = "pendente" if pendente else "validada"

    valor_hora = aula.docente.categoria.valor_hora
    valor_total = horas * valor_hora

    with transaction.atomic():
        aula.sumario = sumario
        aula.tema = tema
        aula.hora_fim_real = agora.time()
        aula.estado = "validada"
        aula.save()

        HorasDocente.objects.update_or_create(
            aula=aula,
            defaults={
                "docente": aula.docente,
                "data": aula.data,
                "horas": horas,
                "valor_hora": valor_hora,
                "valor_total": valor_total,
                "estado": estado_horas,
            },
        )

        registar_auditoria(
            request, "Aula", aula.id, "encerrar_aula",
            detalhes=(f"Estado: em_curso -> validada. Horas: {horas}h x {valor_hora} MT = "
                      f"{valor_total} MT. Horas {estado_horas}. Tema: {tema}."),
        )

    if pendente:
        mensagem = (f"⚠️ Aula encerrada, mas as horas ({horas}h) ficaram abaixo do mínimo "
                    f"({minimo}h) e aguardam aprovação da coordenação.")
    else:
        mensagem = "✅ Aula encerrada e validada!"

    return JsonResponse({
        "sucesso": True,
        "mensagem": mensagem,
        "pendente": pendente,
        "horas": float(horas),
        "valor_hora": float(valor_hora),
        "valor_total": float(valor_total),
    })


# ============================================================
# API AJAX — PEDIR REVISÃO
# ============================================================
@login_required(login_url="login")
@require_POST
def api_pedir_revisao(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)

    if _nao_e_dono(request, aula):
        return _erro_dono(request, aula)

    if aula.estado != "bloqueada":
        return JsonResponse({"erro": "Só pode pedir revisão de uma aula bloqueada."}, status=400)

    motivo = request.POST.get("motivo", "").strip()
    if len(motivo) < 10:
        return JsonResponse({"erro": "Explique o motivo (mínimo 10 caracteres)."}, status=400)

    if PedidoRevisao.objects.filter(aula=aula, estado="pendente").exists():
        return JsonResponse({"erro": "Já existe um pedido pendente para esta aula."}, status=400)

    pedido = PedidoRevisao.objects.create(aula=aula, docente=aula.docente, motivo=motivo)

    registar_auditoria(
        request, "PedidoRevisao", pedido.id, "pedir_revisao",
        detalhes=f"Aula {aula.id}. Motivo: {motivo}",
    )

    return JsonResponse({
        "sucesso": True,
        "mensagem": "✅ Pedido enviado à coordenação. Aguarde a decisão.",
    })