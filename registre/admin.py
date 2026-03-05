from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Structure, ActeNaissance

@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    list_display = ('prefecture', 'sous_prefecture', 'nom_centre')

@admin.register(ActeNaissance)
class ActeNaissanceAdmin(admin.ModelAdmin):
    # 'action_imprimer' remplacera le texte "Lien indisponible" par un bouton vert
    list_display = ('numero_acte_complet', 'nom_enfant', 'prenoms_enfant', 'get_prefecture', 'get_sous_prefecture', 'action_imprimer')
    
    list_select_related = ('structure',)
    list_filter = ('structure__prefecture', 'annee_registre')
    search_fields = ('nom_enfant', 'numero_registre')

    def get_prefecture(self, obj):
        return obj.structure.prefecture
    get_prefecture.short_description = 'PRÉFECTURE'

    def get_sous_prefecture(self, obj):
        return obj.structure.sous_prefecture
    get_sous_prefecture.short_description = 'SOUS-PRÉFECTURE'

    def action_imprimer(self, obj):
        # [span_1](start_span)Utilisation du nom correct identifié dans url.txt[span_1](end_span)
        url_name = 'voir_extrait' 
        
        try:
            # [span_2](start_span)pk est utilisé car c'est ce qui est défini dans votre url.txt[span_2](end_span)
            url = reverse(url_name, kwargs={'pk': obj.pk})
            return format_html(
                '<a class="button" href="{}" target="_blank" '
                'style="background-color: #28a745; color: white; padding: 5px 12px; '
                'border-radius: 4px; text-decoration: none; font-weight: bold; display: inline-block;">'
                'Imprimer</a>', 
                url
            )
        except Exception as e:
            return format_html('<span style="color: red; font-size: 10px;">Erreur lien</span>')
    
    action_imprimer.short_description = 'IMPRESSION'

    # Formulaire de saisie avec les mentions marginales (Mariage, Décès)
    fieldsets = (
        ('Info Admin', {'fields': ('structure', 'numero_registre', 'annee_registre', 'date_declaration')}),
        ('Enfant', {'fields': ('nom_enfant', 'prenoms_enfant', 'date_naissance', 'heure_naissance', 'lieu_naissance')}),
        ('Mentions Marginales', {
            'fields': ('date_mariage', 'conjoint_mariage', 'dissolution_mariage', 'date_deces', 'lieu_deces')
        }),
    )
