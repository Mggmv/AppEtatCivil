from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.apps import apps # Plus sûr pour l'importation

# Page d'accueil intelligente
def home(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin:index')
        return redirect('dashboard')
    return redirect('login')

# Tableau de bord pour les agents et l'administration
@login_required
def dashboard(request):
    # Récupération dynamique du modèle pour éviter l'ImportError
    Naissance = apps.get_model('registre', 'Naissance') 
    derniers_actes = Naissance.objects.all().order_by('-id')[:10]
    return render(request, 'registre/dashboard.html', {'actes': derniers_actes})

# Vue pour voir un extrait spécifique
@login_required
def voir_extrait(request, pk):
    Naissance = apps.get_model('registre', 'Naissance')
    acte = get_object_or_404(Naissance, pk=pk)
    return render(request, 'registre/extrait_naissance.html', {'acte': acte})
