from django.contrib import admin
from django.urls import path, include
from registre import views
from registre.admin import custom_admin_site


urlpatterns = [
    # Page d'accueil (sans /admin/)
    path('', views.home, name='home'),
    
    # Authentification pour les agents
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Administration
     path('admin/', custom_admin_site.urls),
    
    # Vos pages de travail
    path('dashboard/', views.dashboard, name='dashboard'),
    path('extrait/<int:pk>/', views.voir_extrait, name='voir_extrait'),
    
    # NOUVEAU : Exportation du registre vers Excel
    path('exporter-registre/', views.exporter_actes_csv, name='exporter_actes'),

  # Le lien magique pour l'impression du certificat
    path('certificat/<int:certificat_id>/imprimer/', views.imprimer_certificat_residence, name='imprimer_certificat'),
]