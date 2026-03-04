from django.contrib import admin
from django.urls import path, include
from registre import views

urlpatterns = [
    # Accès direct (sans taper admin)
    path('', views.home, name='home'),
    
    # Gestion des comptes (pour vos futurs agents)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Administration Django
    path('admin/', admin.site.urls),
    
    # Tableau de bord des agents
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Vue des extraits
    path('extrait/<int:pk>/', views.voir_extrait, name='voir_extrait'),
]
