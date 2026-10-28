from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
from .models import Docente, Aula, ValidacaoAula, Presenca, Sala, HorasDocente
from .serializers import (
    DocenteSerializer, AulaSerializer, ValidacaoAulaSerializer,
    PresencaSerializer, SalaSerializer, HorasDocenteSerializer
)


class DocenteViewSet(viewsets.ModelViewSet):
    queryset = Docente.objects.all()
    serializer_class = DocenteSerializer

    @action(detail=True, methods=["get"])
    def aulas(self, request, pk=None):
        docente = self.get_object()
        aulas = Aula.objects.filter(docente=docente).order_by("-data", "-hora_inicio")
        return Response(AulaSerializer(aulas, many=True).data)

    @action(detail=True, methods=["get"])
    def horas(self, request, pk=None):
        docente = self.get_object()
        horas = HorasDocente.objects.filter(docente=docente).order_by("-data")
        total_horas = sum(h.horas for h in horas)
        total_valor = sum(h.valor_total for h in horas)
        return Response({
            "docente": docente.nome,
            "total_horas": float(total_horas),
            "total_valor": float(total_valor),
            "detalhes": HorasDocenteSerializer(horas, many=True).data,
        })


class AulaViewSet(viewsets.ModelViewSet):
    queryset = Aula.objects.all().order_by("-data", "-hora_inicio")
    serializer_class = AulaSerializer

    @action(detail=True, methods=["post"])
    def iniciar(self, request, pk=None):
        aula = self.get_object()
        aula.estado = "em_curso"
        aula.hora_inicio_real = timezone.now().time()
        aula.save()
        return Response({
            "mensagem": "Aula iniciada. Aguarda validação de localização.",
            "aula": AulaSerializer(aula).data,
        })

    @action(detail=True, methods=["post"])
    def validar_local(self, request, pk=None):
        aula = self.get_object()
        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")
        qr_lido = request.data.get("qr_code", "")
        wifi_ssid = request.data.get("wifi_ssid", "")

        sala = aula.sala
        sala_validada = False
        recinto_validado = False
        qr_validado = False
        resultado = "bloqueado"

        if qr_lido and qr_lido == sala.qr_code:
            qr_validado = True
            sala_validada = True
            recinto_validado = True
            resultado = "autorizado"
        elif wifi_ssid and wifi_ssid == sala.wifi_ssid:
            sala_validada = True
            recinto_validado = True
            resultado = "autorizado"
        elif latitude and longitude and sala.latitude and sala.longitude:
            from geopy.distance import geodesic
            ponto_docente = (float(latitude), float(longitude))
            ponto_sala = (float(sala.latitude), float(sala.longitude))
            distancia = geodesic(ponto_docente, ponto_sala).meters
            if distancia <= 30:
                recinto_validado = True
                sala_validada = True
                resultado = "autorizado"
            elif distancia <= 100:
                recinto_validado = True

        ValidacaoAula.objects.create(
            aula=aula,
            docente=aula.docente,
            latitude=latitude,
            longitude=longitude,
            sala_validada=sala_validada,
            recinto_validado=recinto_validado,
            horario_validado=True,
            qr_validado=qr_validado,
            resultado=resultado,
        )

        if resultado == "autorizado":
            return Response({
                "resultado": "autorizado",
                "mensagem": "Localização validada. Pode continuar.",
                "sala_validada": True,
                "recinto_validado": True,
            })
        else:
            aula.estado = "bloqueada"
            aula.save()
            return Response({
                "resultado": "bloqueado",
                "mensagem": "Aula bloqueada — o docente não se encontra na sala de aula definida para esta actividade.",
                "sala_prevista": sala.codigo,
                "sala_validada": False,
                "recinto_validado": recinto_validado,
            }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["post"])
    def encerrar(self, request, pk=None):
        aula = self.get_object()
        if aula.estado != "em_curso":
            return Response({"erro": "A aula não está em curso."}, status=status.HTTP_400_BAD_REQUEST)

        sumario = request.data.get("sumario", aula.sumario)
        tema = request.data.get("tema", aula.tema)

        if not sumario or not tema:
            return Response({"erro": "Sumário e tema são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

        if not aula.presencas.exists():
            return Response({"erro": "É necessário registar as presenças antes de encerrar."}, status=status.HTTP_400_BAD_REQUEST)

        aula.sumario = sumario
        aula.tema = tema
        aula.hora_fim_real = timezone.now().time()
        aula.estado = "validada"
        aula.save()

        h_inicio = aula.hora_inicio_real or aula.hora_inicio
        h_fim = aula.hora_fim_real or aula.hora_fim
        dt_inicio = datetime.combine(aula.data, h_inicio)
        dt_fim = datetime.combine(aula.data, h_fim)
        horas = round((dt_fim - dt_inicio).total_seconds() / 3600, 2)

        valor_hora = aula.docente.categoria.valor_hora
        valor_total = horas * valor_hora

        HorasDocente.objects.update_or_create(
            aula=aula,
            defaults={
                "docente": aula.docente,
                "data": aula.data,
                "horas": horas,
                "valor_hora": valor_hora,
                "valor_total": valor_total,
                "estado": "validada",
            }
        )

        return Response({
            "mensagem": "Aula encerrada e validada com sucesso.",
            "horas": float(horas),
            "valor_hora": float(valor_hora),
            "valor_total": float(valor_total),
            "aula": AulaSerializer(aula).data,
        })


class SalaViewSet(viewsets.ModelViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer


class PresencaViewSet(viewsets.ModelViewSet):
    queryset = Presenca.objects.all()
    serializer_class = PresencaSerializer