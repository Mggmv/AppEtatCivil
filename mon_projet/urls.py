from django.contrib import admin
from django.urls import path
from registre.views import apercu_extrait # Import direct pour éviter la boucle

urlpatterns = [
    # Accès à l'administration
    path('admin/', admin.site.urls),
    
    # Lien pour l'impression
    path('extrait/<int:pk>/', apercu_extrait, name='apercu_extrait'),
]