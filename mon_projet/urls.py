from django.contrib import admin
from django.urls import path
from django.contrib.auth import get_user_model
from registre.views import apercu_extrait # Import direct pour éviter la boucle

# --- CODE DE SECOURS POUR CRÉER VOTRE COMPTE ---
try:
    User = get_user_model()
    if not User.objects.filter(username='Mggmv').exists():
        User.objects.create_superuser('Mggmv', 'mgbehe14@gmail.com', 'Gbehe2804')
except Exception:
    pass
# ----------------------------------------------

urlpatterns = [
    # Accès à l'administration
    path('admin/', admin.site.urls),
    
    # Lien pour l'impression
    path('extrait/<int:pk>/', apercu_extrait, name='apercu_extrait'),
]
