from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.apps import apps

@login_required
def dashboard(request):
    try:
        # On tente de récupérer le modèle Naissance
        Naissance = apps.get_model('registre', 'Naissance')
        derniers_actes = Naissance.objects.all().order_by('-id')[:10]
    except (LookupError, Exception):
        # Si le modèle n'existe pas encore, on renvoie une liste vide
        derniers_actes = []
    
    return render(request, 'registre/dashboard.html', {'actes': derniers_actes})

def home(request):
    # Redirige vers le dashboard si connecté, sinon vers le login
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

@login_required
def voir_extrait(request, pk):
    try:
        Naissance = apps.get_model('registre', 'Naissance')
        acte = get_object_or_404(Naissance, pk=pk)
        return render(request, 'registre/extrait_naissance.html', {'acte': acte})
    except:
        return redirect('dashboard')
