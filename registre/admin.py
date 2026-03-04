from django.contrib import admin
from .models import Structure, ActeNaissance

@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    """Configuration pour la gestion des structures (Préfecture, Sous-Préfecture, Centre)"""
    # Affichage en colonnes dans la liste
    list_display = ('prefecture', 'sous_prefecture', 'nom_centre')
    
    # Filtre latéral pour regrouper rapidement par Préfecture
    list_filter = ('prefecture', 'sous_prefecture')
    
    # Barre de recherche
    search_fields = ('prefecture', 'sous_prefecture', 'nom_centre')
    
    ordering = ('prefecture', 'sous_prefecture')

@admin.register(ActeNaissance)
class ActeNaissanceAdmin(admin.ModelAdmin):
    """Configuration pour la gestion des actes avec toutes les mentions marginales"""
    
    # 1. Optimisation de la performance (évite la lenteur)
    list_select_related = ('structure',) 
    list_per_page = 20 # Paging pour éviter de charger trop de données d'un coup
    
    # 2. Affichage de la liste des actes
    list_display = ('numero_acte_complet', 'nom_enfant', 'prenoms_enfant', 'get_prefecture', 'get_sous_prefecture', 'date_declaration')
    
    # 3. Filtres pour le regroupement et les statistiques
    # On utilise 'structure__prefecture' pour filtrer les actes par leur préfecture rattachée
    list_filter = ('structure__prefecture', 'structure__sous_prefecture', 'annee_registre', 'date_declaration')
    
    # 4. Recherche par nom ou numéro d'acte
    search_fields = ('nom_enfant', 'prenoms_enfant', 'numero_registre')

    # 5. Organisation du formulaire de saisie (inclut les mentions marginales)
    fieldsets = (
        ('Informations Administratives', {
            'fields': ('structure', 'numero_registre', 'annee_registre', 'date_declaration')
        }),
        ('Identité de l’Enfant', {
            'fields': ('nom_enfant', 'prenoms_enfant', 'date_naissance', 'heure_naissance', 'lieu_naissance')
        }),
        ('Filiation', {
            'fields': (('nom_pere', 'nationalite_pere'), ('nom_mere', 'nationalite_mere'))
        }),
        ('Mentions Marginales (Éventuellement)', {
            'description': "Toutes les mentions définies dans le modèle sont affichées ici",
            'fields': ('transcription_justice', 'date_mariage', 'conjoint_mariage', 'dissolution_mariage', 'date_deces', 'lieu_deces')
        }),
    )

    # Méthodes pour afficher les informations de la structure dans la liste des actes
    def get_prefecture(self, obj):
        return obj.structure.prefecture
    get_prefecture.short_description = 'Préfecture'

    def get_sous_prefecture(self, obj):
        return obj.structure.sous_prefecture
    get_sous_prefecture.short_description = 'Sous-Préfecture'
