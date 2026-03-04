from django.contrib import admin
from django.urls import path, include
from registre import views

urlpatterns = [
    # Page d'accueil (sans /admin/)
    path('', views.home, name='home'),
    
    # Authentification pour les agents
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Administration
    path('admin/', admin.site.urls),
    
    # Vos pages de travail
    path('dashboard/', views.dashboard, name='dashboard'),
    path('extrait/<int:pk>/', views.voir_extrait, name='voir_extrait'),
]
