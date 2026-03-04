from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Structure, ActeNaissance

@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    list_display = ('nom_centre', 'sous_prefecture')

@admin.register(ActeNaissance)
class ActeNaissanceAdmin(admin.ModelAdmin):
    # Affichage des colonnes dans la liste des actes
    list_display = ('nom_complet_officiel', 'date_naissance', 'lieu_naissance', 'bouton_imprimer')
    search_fields = ('nom_enfant', 'prenoms_enfant')
    list_filter = ('date_naissance', 'structure')

    def bouton_imprimer(self, obj):
        # On remplace 'apercu_extrait' par 'voir_extrait' pour corriger l'erreur NoReverseMatch
        url = reverse('voir_extrait', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank" style="background-color: #28a745; color: white;">Imprimer Extrait</a>', url)

    bouton_imprimer.short_description = 'Action'
    bouton_imprimer.allow_tags = True
