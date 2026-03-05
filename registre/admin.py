from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Structure, ActeNaissance

@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    list_display = ('prefecture', 'sous_prefecture', 'nom_centre')
    list_filter = ('prefecture',)
    search_fields = ('nom_centre', 'prefecture')

@admin.register(ActeNaissance)
class ActeNaissanceAdmin(admin.ModelAdmin):
    # Ajout de 'action_imprimer' dans la liste pour afficher le bouton vert
    list_display = ('numero_acte_complet', 'nom_enfant', 'prenoms_enfant', 'get_prefecture', 'get_sous_prefecture', 'action_imprimer')
    
    # Optimisation pour éviter les erreurs de chargement (OperationalError)
    list_select_related = ('structure',)
    list_filter = ('structure__prefecture', 'structure__sous_prefecture', 'annee_registre')
    search_fields = ('nom_enfant', 'numero_registre')

    def get_prefecture(self, obj):
        return obj.structure.prefecture
    get_prefecture.short_description = 'Préfecture'

    def get_sous_prefecture(self, obj):
        return obj.structure.sous_prefecture
    get_sous_prefecture.short_description = 'Sous-Préfecture'

    # Fonction pour générer le bouton d'impression sur chaque ligne
    def action_imprimer(self, obj):
        # On tente de récupérer l'URL de l'extrait. 
        # Note : Vérifiez que 'extrait_naissance' est bien le nom dans votre urls.py
        try:
            url = reverse('extrait_naissance', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" target="_blank" '
                'style="background-color: #28a745; color: white; padding: 5px 12px; '
                'border-radius: 4px; text-decoration: none; font-weight: bold;">'
                'Imprimer</a>', 
                url
            )
        except:
            return "Lien indisponible"
    
    action_imprimer.short_description = 'Impression'

    # Organisation du formulaire de saisie avec les mentions marginales
    fieldsets = (
        ('Administration', {'fields': ('structure', 'numero_registre', 'annee_registre', 'date_declaration')}),
        ('Enfant', {'fields': ('nom_enfant', 'prenoms_enfant', 'date_naissance', 'heure_naissance', 'lieu_naissance')}),
        ('Mentions Marginales', {
            'fields': ('date_mariage', 'conjoint_mariage', 'dissolution_mariage', 'date_deces', 'lieu_deces')
        }),
    )
