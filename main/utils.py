from django.utils import timezone
from .models import Alianza, Voto
from datetime import datetime

def get_user_status(user):
    """
    Devuelve TODA la info común del usuario:
    - aliado actual
    - id del aliado
    - si tiene alianza activa
    - votos del día (por participante)
    - días aliado
    """

    hoy = timezone.now().date()

    # 1. Obtener alianza activa
    aliado = None
    dias_aliado = 0
    if user.is_authenticated:
        aliado = (
            Alianza.objects
            .filter(usuario=user, fecha_fin__isnull=True)
            .first()
        )

        if aliado:
            dias_aliado = (hoy - aliado.fecha_inicio.date()).days

    # 2. Obtener votos del día
    votos_usuario = {}
    if user.is_authenticated:
        votos = Voto.objects.filter(usuario=user, fecha__date=hoy)
        votos_usuario = {v.participante.id: True for v in votos}

    return {
        "aliado": aliado,
        "es_aliado": aliado is not None,
        "id_aliado": aliado.participante.id if aliado else None,
        "dias_aliado": dias_aliado,
        "votos_usuario": votos_usuario,
    }
