from django.shortcuts import render, get_object_or_404, redirect
from .models import Participante, VideoTop, Reto, Voto, Alianza
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, RegistroForm
from datetime import date
from django.utils import timezone
from .utils import get_user_status


def home(request):
    participantes = Participante.objects.all().order_by('-puntos_totales')
    info = get_user_status(request.user)

    context = {
        'participantes': participantes,
        **info   # <--- unimos toda la info del utils
    }
    return render(request, 'main/home.html', context)



def participantes(request):
    participantes = Participante.objects.all().order_by('-puntos_totales')
    info = get_user_status(request.user)

    context = {
        'participantes': participantes,
        **info   # <--- unimos toda la info del utils
    }
    return render(request, 'main/participantes.html', context)

def participante_detalle(request, pk):
    participante = get_object_or_404(Participante, pk=pk)
    videos = VideoTop.objects.filter(participante=participante)
    retos = Reto.objects.filter(participante=participante).order_by('-fecha')

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
        'ha_votado': ha_votado,
    })
def votar(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')

    participante = Participante.objects.get(pk=pk)

    # Intentamos crear voto
    try:
        Voto.objects.create(
            usuario=request.user,
            participante=participante,
            fecha=timezone.now()
        )
        participante.votos_recibidos += 1
        participante.puntos_totales += 10  # ejemplo
        participante.save()

    except:
        pass  # ya votó hoy

    return redirect('participante_detalle', pk=pk)

def aliarse(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')

    participante = Participante.objects.get(pk=pk)

    # Romper alianzas previas activas del usuario
    Alianza.objects.filter(
        usuario=request.user, 
        fecha_fin__isnull=True
        ).update(fecha_fin=timezone.now())

    # Crear la nueva
    Alianza.objects.create(
        usuario=request.user,
        participante=participante,
        fecha_inicio=timezone.now()
    )

    return redirect('participante_detalle', pk=pk)



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


def donar_puntos(request, objetivo_id):
    if not request.user.is_authenticated:
        return redirect("login")

    objetivo = get_object_or_404(ObjetivoDonacion, id=objetivo_id)

    if request.method == "POST":
        cantidad = int(request.POST.get("puntos", 0))

        # registrar o actualizar la donación del usuario
        reg, creado = DonacionUsuario.objects.get_or_create(
            usuario=request.user,
            objetivo=objetivo
        )
        reg.puntos_donados += cantidad
        reg.save()

        # sumar al objetivo
        objetivo.puntos_actuales += cantidad

        # comprobar si se completó
        if objetivo.puntos_actuales >= objetivo.puntos_necesarios:
            objetivo.activo = False

        objetivo.save()

        return redirect("playground")
