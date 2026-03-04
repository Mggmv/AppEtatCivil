from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Naissance

# 1. PAGE D'ACCUEIL (Redirection intelligente)
def home(request):
    if request.user.is_authenticated:
        # Si c'est l'administrateur, on peut l'envoyer vers l'admin ou un tableau de bord
        if request.user.is_superuser:
            return redirect('admin:index')
        # Pour les autres utilisateurs (agents), on les envoie vers le tableau de bord
        return redirect('dashboard')
    # Si non connecté, direction la page de login
    return redirect('login')

# 2. TABLEAU DE BORD POUR LES AGENTS
@login_required
def dashboard(request):
    # Liste des 10 derniers actes pour l'agent
    derniers_actes = Naissance.objects.all().order_by('-id')[:10]
    return render(request, 'registre/dashboard.html', {'actes': derniers_actes})

# 3. VOTRE VUE EXISTANTE (Aperçu de l'extrait)
@login_required
def voir_extrait(request, pk):
    acte = get_object_or_404(Naissance, pk=pk)
    return render(request, 'registre/extrait_naissance.html', {'acte': acte})
