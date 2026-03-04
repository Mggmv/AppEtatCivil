from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.apps import apps

@login_required
def dashboard(request):
    try:
        # On essaie de récupérer le modèle 'Naissance'
        Naissance = apps.get_model('registre', 'Naissance')
        derniers_actes = Naissance.objects.all().order_by('-id')[:10]
    except (LookupError, LookupError):
        # Si le modèle n'existe pas encore ou porte un autre nom, on affiche une liste vide
        derniers_actes = []
    
    return render(request, 'registre/dashboard.html', {'actes': derniers_actes})

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

# Conservez votre vue voir_extrait actuelle mais avec le try/except si besoin
