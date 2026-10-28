import ipaddress

from .models import Auditoria


def ip_cliente(request):
    """Devolve o IP do pedido (ou None se não for um IP válido)."""
    bruto = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
    if not bruto:
        bruto = request.META.get("REMOTE_ADDR", "")
    try:
        ipaddress.ip_address(bruto)
        return bruto
    except ValueError:
        return None


def registar_auditoria(request, entidade, entidade_id, operacao, detalhes="", localizacao=""):
    """
    Grava uma linha na tabela Auditoria (RN12):
    utilizador, IP, data/hora (automática), localização, ação e detalhes.
    """
    utilizador = request.user if request.user.is_authenticated else None
    return Auditoria.objects.create(
        utilizador=utilizador,
        entidade=entidade,
        entidade_id=entidade_id or 0,
        operacao=operacao,
        ip=ip_cliente(request),
        localizacao=(localizacao or "")[:200],
        detalhes=detalhes or "",
    )
