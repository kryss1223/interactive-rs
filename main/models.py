from django.db import models
from django.contrib.auth.models import User, AbstractUser  # 👈 Usamos el modelo base
from django.utils import timezone

class User(AbstractUser):
    nickname = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    puntos = models.IntegerField(default=0)

    USERNAME_FIELD = 'username'  # Puedes cambiarlo a 'nickname' si prefieres
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.nickname
# ───────────────────────────────
# PERFIL (extiende al User)
# ───────────────────────────────
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50, unique=True)
    puntos = models.IntegerField(default=0)

    def __str__(self):
        return self.nickname


# ───────────────────────────────
# PARTICIPANTE
# ───────────────────────────────
class Participante(models.Model):
    nombre = models.CharField(max_length=100)
    instagram = models.URLField(blank=True, null=True)
    tiktok = models.URLField(blank=True, null=True)
    votos_recibidos = models.IntegerField(default=0)
    puntos_totales = models.IntegerField(default=0)
    eliminado = models.BooleanField(default=False)

    foto = models.ImageField(
        upload_to='participantes/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nombre


# ───────────────────────────────
# ALIANZAS
# ───────────────────────────────
class Alianza(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('usuario', 'fecha_inicio')

    def __str__(self):
        return f"{self.usuario.username} aliado con {self.participante.nombre}"


# ───────────────────────────────
# DONACIONES
# ───────────────────────────────
class Donacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.usuario.username} donó {self.cantidad} a {self.participante.nombre}"


class ObjetivoDonacion(models.Model):
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)

    puntos_necesarios = models.IntegerField(default=100)
    puntos_actuales = models.IntegerField(default=0)

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def progreso(self):
        return int((self.puntos_actuales / self.puntos_necesarios) * 100)

    def __str__(self):
        return f"{self.participante.nombre}: {self.titulo}"

class DonacionUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    objetivo = models.ForeignKey(ObjetivoDonacion, on_delete=models.CASCADE)
    puntos_donados = models.IntegerField(default=0)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'objetivo')

# ───────────────────────────────
# VOTOS
# ───────────────────────────────
class Voto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('usuario', 'fecha')

    def __str__(self):
        return f"{self.usuario.username} votó a {self.participante.nombre}"


# ───────────────────────────────
# RETOS
# ───────────────────────────────
class Reto(models.Model):
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
    texto = models.TextField()
    puntos = models.IntegerField(default=0)
    completado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Reto de {self.participante.nombre} ({self.fecha.date()})"


# ───────────────────────────────
# VIDEOS TOP
# ───────────────────────────────
class VideoTop(models.Model):
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    fecha_subida = models.DateTimeField(default=timezone.now)
    url_video = models.URLField()

    def __str__(self):
        return f"Top video de {self.participante.nombre}"


# ───────────────────────────────
# ENCUESTAS
# ───────────────────────────────
class Encuesta(models.Model):
    pregunta = models.CharField(max_length=300)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class OpcionEncuesta(models.Model):
    encuesta = models.ForeignKey(Encuesta, related_name="opciones", on_delete=models.CASCADE)
    texto = models.CharField(max_length=200)
    votos = models.IntegerField(default=0)

    def __str__(self):
        return self.texto

# ───────────────────────────────
# RETOS USUARIO
# ───────────────────────────────
class RetoUsuario(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    puntos_recompensa = models.IntegerField(default=10)
    activo = models.BooleanField(default=True)

    # tipo de reto: votación, alianza, constancia...
    tipo = models.CharField(max_length=50, choices=[
        ('votar', 'Votar'),
        ('alianza', 'Alianza'),
        ('constancia', 'Constancia'),
    ])

    # param extra (ej: “3 votaciones”, “2 días”, etc)
    parametro = models.IntegerField(default=1)
