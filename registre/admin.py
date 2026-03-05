from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Structure, ActeNaissance

@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    # Affichage des colonnes dans la liste des structures
    list_display = ('prefecture', 'sous_prefecture', 'nom_centre')
    search_fields = ('prefecture', 'sous_prefecture', 'nom_centre')

@admin.register(ActeNaissance)
class ActeNaissanceAdmin(admin.ModelAdmin):
    # Configuration des colonnes du tableau de bord
    # 'action_imprimer' affiche le bouton vert à la place du texte d'erreur
    list_display = (
        'numero_acte_complet', 
        'nom_enfant', 
        'prenoms_enfant', 
        'get_prefecture', 
        'get_sous_prefecture', 
        'action_imprimer'
    )
    
    list_filter = ('structure__prefecture', 'annee_registre', 'date_declaration')
    search_fields = ('nom_enfant', 'numero_registre')
    list_select_related = ('structure',)

    # Récupération de la Préfecture depuis le modèle Structure
    def get_prefecture(self, obj):
        return obj.structure.prefecture
    get_prefecture.short_description = 'PRÉFECTURE'

    # Récupération de la Sous-Préfecture depuis le modèle Structure
    def get_sous_prefecture(self, obj):
        return obj.structure.sous_prefecture
    get_sous_prefecture.short_description = 'SOUS-PRÉFECTURE'

    # Création du bouton Imprimer vert
    def action_imprimer(self, obj):
        try:
            # Utilisation du nom 'voir_extrait' défini dans votre fichier url.txt
            url = reverse('voir_extrait', kwargs={'pk': obj.pk})
            return format_html(
                '<a class="button" href="{}" target="_blank" '
                'style="background-color: #28a745; color: white; padding: 5px 12px; '
                'border-radius: 4px; text-decoration: none; font-weight: bold; '
                'display: inline-block; min-width: 80px; text-align: center;">'
                'Imprimer</a>', 
                url
            )
        except Exception:
            # Si l'URL n'est pas trouvée, on garde un message discret
            return format_html('<span style="color: #999;">Lien indisponible</span>')
    
    action_imprimer.short_description = 'IMPRESSION'

    # Organisation des champs dans le formulaire de saisie
    fieldsets = (
        ('Enregistrement', {
            'fields': ('structure', 'numero_registre', 'annee_registre', 'date_declaration')
        }),
        ('Identité de l\'enfant', {
            'fields': ('nom_enfant', 'prenoms_enfant', 'date_naissance', 'heure_naissance', 'lieu_naissance')
        }),
        ('Filiation', {
            'fields': ('nom_pere', 'nationalite_pere', 'nom_mere', 'nationalite_mere')
        }),
        ('Mentions Marginales', {
            'classes': ('collapse',), # Le volet est réduit par défaut
            'fields': ('date_mariage', 'conjoint_mariage', 'dissolution_mariage', 'date_deces', 'lieu_deces'),
            'description': 'Remplir uniquement en cas de mise à jour de l\'acte.'
        }),
    )
