# registre/context_processors.py
from .models import Structure

def infos_structure(request):
    try:
        # On va chercher la première structure enregistrée dans la base de données
        structure = Structure.objects.first()
        
        if structure and structure.sous_prefecture:
            nom = f"Sous-Préfecture de {structure.sous_prefecture}"
        else:
            nom = "Sous-Préfecture"
    except Exception:
        # Sécurité au cas où la base de données est vide ou pas encore migrée
        nom = "Sous-Préfecture"
        
    return {'nom_structure_dynamique': nom}