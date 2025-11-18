from django.contrib import admin
from .models import User, Participante, Alianza, RetoUsuario,  Encuesta, OpcionEncuesta, DonacionUsuario,  ObjetivoDonacion, Donacion, Voto, Reto, VideoTop

# Register your models here.
admin.site.register(User)

admin.site.register(Alianza)
admin.site.register(ObjetivoDonacion)
admin.site.register(DonacionUsuario)
admin.site.register(Encuesta)
admin.site.register(OpcionEncuesta)
admin.site.register(RetoUsuario)

admin.site.register(Voto)
admin.site.register(Reto)
admin.site.register(VideoTop)

@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'puntos_totales', 'votos_recibidos', 'preview_foto')

    def preview_foto(self, obj):
        if obj.foto:
            return f"<img src='{obj.foto.url}' width='50' height='50' style='border-radius:8px;'>"
        return "Sin foto"
    
    preview_foto.allow_tags = True
    preview_foto.short_description = "Foto"