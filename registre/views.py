from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ActeNaissance

def home(request):
    """Indispensable pour corriger l'erreur : module 'views' has no attribute 'home'"""
    return render(request, 'registre/home.html')

@login_required
def dashboard(request):
    """Indispensable pour corriger l'erreur : module 'views' has no attribute 'dashboard'"""
    actes = ActeNaissance.objects.all().order_by('-date_declaration')
    return render(request, 'registre/dashboard.html', {'actes': actes})

@login_required
def voir_extrait(request, pk):
    acte = get_object_or_404(ActeNaissance, pk=pk)
    
    # --- Traitement de la Date et de l'Heure ---
    [span_1](start_span)date_lettres = acte.infos_naissance_lettres() # Utilise 'mil' et 'premier'[span_1](end_span)
    phrase_naissance = f"Le {date_lettres}"
    
    if acte.heure_naissance:
        h = acte.heure_naissance.hour
        m = acte.heure_naissance.minute
        conv = {
            0: "zéro", 1: "une", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq",
            6: "six", 7: "sept", 8: "huit", 9: "neuf", 10: "dix",
            11: "onze", 12: "douze", 13: "treize", 14: "quatorze", 15: "quinze",
            16: "seize", 17: "dix-sept", 18: "dix-huit", 19: "dix-neuf", 20: "vingt",
            21: "vingt et une", 22: "vingt-deux", 23: "vingt-trois", 30: "trente",
            40: "quarante", 50: "cinquante"
        }
        txt_h = conv.get(h, str(h)) + (" heure" if h <= 1 else " heures")
        txt_m = ""
        if m > 0:
            if m <= 20 or m in [30, 40, 50]:
                txt_m = " " + conv.get(m)
            else:
                d, u = divmod(m, 10)
                txt_m = f" {conv.get(d*10)}{' et ' if u == 1 else '-'}{conv.get(u)}"
        phrase_naissance += f" à {txt_h}{txt_m}"

    # --- Traitement de la Filiation (Père et Mère) ---
    # Logique pour le Père
    if acte.nom_pere:
        pere_info = acte.nom_pere
        if acte.nationalite_pere:
            [span_2](start_span)pere_info += f" de nationalité {acte.nationalite_pere}"[span_2](end_span)
        pere_label = "Fils de "
    else:
        pere_info = "de père inconnu"
        pere_label = ""

    # Logique pour la Mère
    if acte.nom_mere:
        mere_info = acte.nom_mere
        if acte.nationalite_mere:
            [span_3](start_span)mere_info += f" de nationalité {acte.nationalite_mere}"[span_3](end_span)
        mere_label = "et de "
    else:
        mere_info = "de mère inconnue"
        mere_label = "et "

    context = {
        'acte': acte,
        'date_heure_complete': phrase_naissance,
        'pere_info': pere_info,
        'pere_label': pere_label,
        'mere_info': mere_info,
        'mere_label': mere_label,
    }
    return render(request, 'registre/extrait_naissance.html', context)
