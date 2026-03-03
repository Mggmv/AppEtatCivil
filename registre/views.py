from django.shortcuts import render, get_object_or_404
from .models import ActeNaissance

def apercu_extrait(request, pk):
    acte = get_object_or_404(ActeNaissance, pk=pk)
    # On récupère le dictionnaire contenant la date et l'heure
    infos = acte.infos_naissance_lettres() 
    
    return render(request, 'registre/extrait_naissance.html', {
        'acte': acte,
        'nom_complet': acte.nom_complet_officiel(),
        'date_lettres': infos['date'],
        'heure_lettres': infos['heure'],
    })