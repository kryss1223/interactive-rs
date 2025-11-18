from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('participantes/', views.participantes, name='participantes'),
    path('participante/<int:pk>/', views.participante_detalle, name='participante_detalle'),
    path('votar/<int:pk>/', views.votar, name='votar'),
    path('aliarse/<int:pk>/', views.aliarse, name='aliarse'),
    path("playground/", views.playground, name="playground"),
    path("donar/<int:objetivo_id>/", views.donar_puntos, name="donar_puntos"),

]
