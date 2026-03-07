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

# Vue pour l'affichage de l'extrait officiel
@login_required
def voir_extrait(request, pk):
    acte = get_object_or_404(ActeNaissance, pk=pk)
    
    # 1. Récupération de la date (gère 'mil' et 'premier')
    date_lettres = acte.infos_naissance_lettres()
    
    # 2. Gestion de l'heure
    if acte.heure_naissance:
        h = acte.heure_naissance.hour
        m = acte.heure_naissance.minute
        
        # Dictionnaire simple pour l'heure
        nombres = {
            0: "zéro", 1: "une", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq",
            6: "six", 7: "sept", 8: "huit", 9: "neuf", 10: "dix",
            11: "onze", 12: "douze", 13: "treize", 14: "quatorze", 15: "quinze",
            16: "seize", 17: "dix-sept", 18: "dix-huit", 19: "dix-neuf", 20: "vingt",
            21: "vingt et une", 22: "vingt-deux", 23: "vingt-trois", 30: "trente",
            40: "quarante", 50: "cinquante"
        }
        
        heure_texte = nombres.get(h, str(h)) + (" heure" if h <= 1 else " heures")
        minute_texte = ""
        if m > 0:
            if m <= 20 or m in [30, 40, 50]:
                minute_texte = " " + nombres.get(m)
            else:
                dizaine = (m // 10) * 10
                unite = m % 10
                minute_texte = f" {nombres.get(dizaine)}{' et ' if unite == 1 else '-'}{nombres.get(unite)}"
        
        # Concaténation : "Le [Date] à [Heure]"
        date_heure_complete = f"Le {date_lettres} à {heure_texte}{minute_texte}"
    else:
        # Si l'heure est vide, on ne met que la date
        date_heure_complete = f"Le {date_lettres}"

    context = {
        'acte': acte,
        'date_heure_complete': date_heure_complete,
    }
    return render(request, 'registre/extrait_naissance.html', context)
