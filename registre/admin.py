from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Structure, ActeNaissance

@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    list_display = ('prefecture', 'sous_prefecture', 'nom_centre')

@admin.register(ActeNaissance)
class ActeNaissanceAdmin(admin.ModelAdmin):
    list_display = ('numero_acte_complet', 'nom_enfant', 'prenoms_enfant', 'action_imprimer')
    list_filter = ('structure__prefecture', 'annee_registre')
    
    def action_imprimer(self, obj):
        try:
            [span_4](start_span)url = reverse('voir_extrait', kwargs={'pk': obj.pk}) #[span_4](end_span)
            return format_html(
                '<a class="button" href="{}" target="_blank" '
                'style="background-color: #28a745; color: white; padding: 5px 12px; '
                'border-radius: 4px; text-decoration: none; font-weight: bold;">'
                'Imprimer</a>', url)
        except:
            return "Lien indisponible"
    action_imprimer.short_description = 'IMPRESSION'

    fieldsets = (
        ('1. Registre', {'fields': ('structure', 'numero_registre', 'annee_registre', 'date_declaration')}),
        ('2. L\'Enfant', {'fields': ('nom_enfant', 'prenoms_enfant', 'date_naissance', 'heure_naissance', 'lieu_naissance')}),
        ('3. Filiation', {'fields': (('nom_pere', 'nationalite_pere'), ('nom_mere', 'nationalite_mere'))}),
        ('4. Transcription', {'fields': ('transcription_justice',)}),
        ('5. Mentions Marginales', {
            'classes': ('collapse',), 
            'fields': ('date_mariage', 'conjoint_mariage', 'dissolution_mariage', 'date_deces', 'lieu_deces')
        }),
    )
