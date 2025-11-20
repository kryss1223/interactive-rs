from django.shortcuts import render, get_object_or_404, redirect
from .models import Participante, VideoTop, Reto, Voto, Alianza
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, RegistroForm
from datetime import date
from django.utils import timezone
from django.contrib import messages
from .utils import get_user_status


def home(request):
    participantes = Participante.objects.all().order_by('-puntos_totales')
    info = get_user_status(request.user)

    #AFINIDAD PUBLICO Participante
    # Obtener el valor más alto
    if participantes:
        top_votos = participantes[0].votos_recibidos
    else:
        top_votos = 1  # para evitar división por cero

    # Calcular afinidad por cada participante
    for p in participantes:
        if top_votos > 0:
            p.afinidad = round((p.votos_recibidos / top_votos) * 100, 2)
        else:
            p.afinidad = 0

    top_videos = VideoTop.objects.all().order_by('-fecha_subida')

    context = {
        'participantes': participantes,
        'top_videos': top_videos,
        **info   # <--- unimos toda la info del utils
    }
    return render(request, 'main/home.html', context)



def participantes(request):
    participantes = Participante.objects.all().order_by('-puntos_totales')
    info = get_user_status(request.user)
    
    # Añadir aliados activos para cada participante
    for p in participantes:
        p.numero_aliados = Alianza.objects.filter(
            participante=p, 
            fecha_fin__isnull=True
        ).count()

    context = {
        'participantes': participantes,
        **info   # <--- unimos toda la info del utils
    }
    return render(request, 'main/participantes.html', context)

def participante_detalle(request, pk):
    participante = get_object_or_404(Participante, pk=pk)
    videos = VideoTop.objects.filter(participante=participante)
    retos = Reto.objects.filter(participante=participante).order_by('-fecha')
    numero_aliados = Alianza.objects.filter(participante=participante, fecha_fin__isnull=True).count()

    user = request.user if request.user.is_authenticated else None

    # ¿Es aliado de este participante?
    alianza = None
    if user:
        alianza = Alianza.objects.filter(
            usuario=user,
            participante=participante,
            fecha_fin__isnull=True  # alianza activa
        ).first()

    # ¿Ha votado hoy?
    ha_votado = False
    if user:
        ha_votado = Voto.objects.filter(
            usuario=user,
            participante=participante,
            fecha__date=date.today()
        ).exists()


    return render(request, 'main/participante_detalle.html', {
        'p': participante,
        'videos': videos,
        'retos': retos,
        'alianza': alianza,
        'numero_aliados': numero_aliados,
        'ha_votado': ha_votado,
    })

COSTE_VOTO = 10

def votar(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')

    usuario = request.user
    participante = get_object_or_404(Participante, pk=pk)

    # 1. Comprobar puntos suficientes
    if usuario.puntos < COSTE_VOTO:
        messages.error(request, "No tienes puntos suficientes para votar.")
        return redirect('participante_detalle', pk=pk)

    # 2. Evitar voto duplicado el mismo día
    ya_voto_hoy = Voto.objects.filter(
        usuario=usuario,
        participante=participante,
        fecha__date=timezone.now().date()
    ).exists()

    if ya_voto_hoy:
        messages.error(request, "Ya votaste hoy a este participante.")
        return redirect('participante_detalle', pk=pk)

    # 3. Restar puntos al usuario
    usuario.puntos -= COSTE_VOTO
    usuario.save()

    # 4. Registrar el voto y sumar puntos al participante
    Voto.objects.create(
        usuario=usuario,
        participante=participante,
        fecha=timezone.now()
    )

    participante.votos_recibidos += 1
    participante.puntos_totales += 10  # si quieres que solo valga 1 voto = 10 pts
    participante.save()

    messages.success(request, f"Has votado (-{COSTE_VOTO} puntos)")
    return redirect('participante_detalle', pk=pk)
COSTE_ALIANZA = 50

def aliarse(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')

    usuario = request.user
    participante = get_object_or_404(Participante, pk=pk)

    # 1. Comprobar puntos
    if usuario.puntos < COSTE_ALIANZA:
        messages.error(request, "No tienes puntos suficientes para aliarte.")
        return redirect('participante_detalle', pk=pk)

    # 2. Cerrar alianzas actuales
    Alianza.objects.filter(
        usuario=usuario,
        fecha_fin__isnull=True
    ).update(fecha_fin=timezone.now())

    # 3. Restar puntos
    usuario.puntos -= COSTE_ALIANZA
    usuario.save()

    # 4. Crear nueva alianza
    Alianza.objects.create(
        usuario=usuario,
        participante=participante,
        fecha_inicio=timezone.now()
    )

    messages.success(request, f"Ahora eres aliado de {participante.nombre} (-{COSTE_ALIANZA} puntos)")
    return redirect('participante_detalle', pk=pk)

def donar_puntos(request, objetivo_id):
    if not request.user.is_authenticated:
        return redirect("login")

    usuario = request.user
    objetivo = get_object_or_404(ObjetivoDonacion, id=objetivo_id)

    if request.method == "POST":
        cantidad = int(request.POST.get("puntos", 0))

        # 1. Validación
        if cantidad <= 0:
            messages.error(request, "Debes donar una cantidad válida.")
            return redirect("playground")

        # 2. Comprobar puntos suficientes
        if usuario.puntos < cantidad:
            messages.error(request, "No tienes suficientes puntos.")
            return redirect("playground")

        # 3. Consumir puntos del usuario
        usuario.puntos -= cantidad
        usuario.save()

        # 4. Registrar donación
        reg, creado = DonacionUsuario.objects.get_or_create(
            usuario=usuario,
            objetivo=objetivo
        )
        reg.puntos_donados += cantidad
        reg.save()

        # 5. Actualizar objetivo
        objetivo.puntos_actuales += cantidad

        if objetivo.puntos_actuales >= objetivo.puntos_necesarios:
            objetivo.activo = False

        objetivo.save()

        messages.success(request, f"Has donado {cantidad} puntos.")
        return redirect("playground")


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  
    else:
        form = LoginForm()
    return render(request, 'main/login.html', {'form': form})


def registro_view(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistroForm()

    return render(request, 'main/registro.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')




from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import (
    Participante,
    ObjetivoDonacion,
    DonacionUsuario,
    Reto
)
from .utils import get_user_status


def playground(request):
    # Info general del usuario (alianza, votos, etc.)
    info = get_user_status(request.user)

    # Participantes eliminados
    eliminados = Participante.objects.filter(eliminado=True)

    # Reto activo (ejemplo: el reto más reciente)
    retos_participantes = Reto.objects.all().order_by('-fecha')

    # Objetivos colectivos activos (donaciones)
    objetivos = ObjetivoDonacion.objects.filter(activo=True)


    context = {
        **info,
        "eliminados": eliminados,
        "retos_participantes": retos_participantes,
        "objetivos": objetivos
    }

    return render(request, "main/playground.html", context)



