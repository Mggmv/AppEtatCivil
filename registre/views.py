from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ActeNaissance  # Utilisation du nom exact du modèle

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

# Vue pour l'affichage et l'impression de l'extrait
@login_required
def voir_extrait(request, pk):
    # Récupération de l'acte ou erreur 404 si inconnu
    acte = get_object_or_404(ActeNaissance, pk=pk)
    
    # Appel de la fonction du modèle pour convertir date et heure en lettres
    # Cette fonction applique les règles ivoiriennes : 'mil' et 'premier' [cite: 2026-02-28]
    infos = acte.infos_naissance_lettres()
    
    context = {
        'acte': acte,
        'date_lettres': infos['date'], # Transmis à {{ date_lettres }} dans l'HTML
        'heure_lettres': infos['heure'] # Transmis à {{ heure_lettres }} dans l'HTML
    }
    
    return render(request, 'registre/extrait_naissance.html', context)
