from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Structure, ActeNaissance

@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    list_display = ('nom_centre', 'sous_prefecture')

@admin.register(ActeNaissance)
class ActeNaissanceAdmin(admin.ModelAdmin):
    # Optimisation : on ne garde que l'essentiel pour l'affichage rapide
    list_display = ('id_affiche', 'nom_enfant', 'prenoms_enfant', 'date_declaration', 'bouton_imprimer')
    
    # Ajout de la pagination pour ne pas charger trop d'actes d'un coup
    list_per_page = 20 
    
    # Recherche rapide
    search_fields = ('nom_enfant', 'prenoms_enfant')

    def id_affiche(self, obj):
        # Format demandé : 01 du 12/01/2014
        return f"{obj.id} du {obj.date_declaration.strftime('%d/%m/%Y')}"
    id_affiche.short_description = 'N° Acte'

    def bouton_imprimer(self, obj):
        # On utilise voir_extrait car apercu_extrait cause une erreur 404
        url = reverse('voir_extrait', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" target="_blank" '
            'style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 4px;">'
            'Imprimer</a>', 
            url
        )
    bouton_imprimer.short_description = 'Impression'
