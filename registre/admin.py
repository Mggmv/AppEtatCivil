from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ActeNaissance, Structure # Correction de l'import

@admin.register(ActeNaissance)
class ActeNaissanceAdmin(admin.ModelAdmin):
    list_display = ('numero_acte_complet', 'nom_enfant', 'prenoms_enfant')
    readonly_fields = ('bouton_imprimer_fixe',)

    def bouton_imprimer_fixe(self, obj):
        if obj.id:
            url = reverse('apercu_extrait', args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" '
                'style="position: fixed; bottom: 30px; right: 30px; z-index: 9999; '
                'background: #28a745; color: white; padding: 15px 25px; '
                'border-radius: 50px; text-decoration: none; font-weight: bold; '
                'box-shadow: 0 4px 10px rgba(0,0,0,0.3); border: 2px solid white;">'
                '🖨️ IMPRIMER L\'EXTRAIT</a>', url
            )
        return "Enregistrez d'abord l'acte"

    bouton_imprimer_fixe.short_description = "Action d'Impression"

admin.site.register(Structure)