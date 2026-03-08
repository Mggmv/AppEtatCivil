from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ActeNaissance

@login_required
def voir_extrait(request, pk):
    acte = get_object_or_404(ActeNaissance, pk=pk)
    
    # 1. Gestion de la Date et l'Heure concaténées
    date_lettres = acte.infos_naissance_lettres() # Utilise 'mil' et 'premier'
    complement_heure = ""
    
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
                d = (m // 10) * 10
                u = m % 10
                txt_m = f" {conv.get(d)}{' et ' if u == 1 else '-'}{conv.get(u)}"
        complement_heure = f" à {txt_h}{txt_m}"
    
    date_heure_complete = f"Le {date_lettres}{complement_heure}"

    # 2. Concaténation des Parents et Nationalités
    def formater_parent(nom, nationalite):
        if not nom: return "..........."
        if nationalite:
            return f"{nom} de nationalité {nationalite}"
        return nom

    pere_info = formater_parent(acte.nom_pere, getattr(acte, 'nationalite_pere', None))
    mere_info = formater_parent(acte.nom_mere, getattr(acte, 'nationalite_mere', None))

    context = {
        'acte': acte,
        'date_heure_complete': date_heure_complete,
        'pere_info': pere_info,
        'mere_info': mere_info,
    }
    return render(request, 'registre/extrait_naissance.html', context)
