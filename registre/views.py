from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ActeNaissance

# Page d'accueil : redirige selon l'état de connexion
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

# Tableau de bord pour les agents
@login_required
def dashboard(request):
    # Récupère les 10 derniers actes pour les afficher dans le tableau
    derniers_actes = ActeNaissance.objects.all().order_by('-id')[:10]
    return render(request, 'registre/dashboard.html', {'actes': derniers_actes})

# Vue corrigée pour l'affichage de l'extrait (Supprime la page jaune)
@login_required
def voir_extrait(request, pk):
    # Récupération de l'acte ou erreur 404 si inconnu
    acte = get_object_or_404(ActeNaissance, pk=pk)
    
    # On récupère la date en lettres directement depuis le modèle.
    # Cette fonction applique déjà 'mil' et 'premier'
    date_en_lettres = acte.infos_naissance_lettres()
    
    context = {
        'acte': acte,
        'date_lettres': date_en_lettres, # Variable corrigée
    }
    
    return render(request, 'registre/extrait_naissance.html', context)
