from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ActeNaissance

def home(request):
    """Ajout de cette fonction pour corriger l'AttributeError au déploiement"""
    return render(request, 'registre/home.html')

@login_required
def voir_extrait(request, pk):
    acte = get_object_or_404(ActeNaissance, pk=pk)
    
    # 1. DATE ET HEURE EN LETTRES
    date_lettres = acte.infos_naissance_lettres()
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
        [span_1](start_span)phrase_naissance += f" à {txt_h}{txt_m}"[span_1](end_span)

    # 2. FILIATION (Père et Mère)
    # Logique Père
    if acte.nom_pere:
        nat_p = getattr(acte, 'nationalite_pere', None)
        pere_info = f"{acte.nom_pere} de nationalité {nat_p}" if nat_p else acte.nom_pere
        pere_label = "Fils de "
    else:
        pere_info = "de père inconnu"
        pere_label = ""

    # Logique Mère
    if acte.nom_mere:
        nat_m = getattr(acte, 'nationalite_mere', None)
        mere_info = f"{acte.nom_mere} de nationalité {nat_m}" if nat_m else acte.nom_mere
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
