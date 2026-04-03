import os
import csv
import datetime
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.db.models import Q, Case, When, Value, IntegerField
from .models import Structure, ActeNaissance, CertificatResidence

@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    list_display = ('region', 'prefecture', 'sous_prefecture', 'nom_centre')

# ==========================================
# 1. GESTION DES ACTES DE NAISSANCE
# ==========================================
@admin.register(ActeNaissance)
class ActeNaissanceAdmin(admin.ModelAdmin):
    list_display = ('numero_acte_complet', 'nom_enfant', 'prenoms_enfant', 'sexe', 'action_imprimer')
    list_filter = ('sexe', 'date_declaration', 'structure')

    # --- L'ORGANISATION DU FORMULAIRE D'ENREGISTREMENT --- 
    fieldsets = (
        ('1. Registre', {'fields': ('structure', 'numero_registre', 'annee_registre', 'date_declaration')}),
        ('2. L\'Enfant', {'fields': ('nom_enfant', 'prenoms_enfant', 'sexe', 'date_naissance', 'heure_naissance', 'lieu_naissance')}),
        ('3. Filiation', {'fields': (('nom_pere', 'nationalite_pere'), ('nom_mere', 'nationalite_mere'))}),
        ('4. Transcription', {'fields': ('transcription_justice',)}),
        ('5. Mentions Marginales', {
            'classes': ('collapse',), 
            'fields': ('date_mariage', 'conjoint_mariage', 'dissolution_mariage', 'date_deces', 'lieu_deces')
        }),
    )

    # --- BOUTON IMPRIMER --- 
    def action_imprimer(self, obj):
        try:
            url = reverse('voir_extrait', kwargs={'pk': obj.pk})
            return format_html(
                '<a class="button" href="{}" target="_blank" '
                'style="background-color: #28a745; color: white; padding: 5px 12px; '
                'border-radius: 4px; text-decoration: none; font-weight: bold;">Imprimer</a>', 
                url
            )
        except Exception:
            return "Lien indisponible"
    action_imprimer.short_description = 'IMPRESSION'

    # --- NOTRE OUTIL D'EXPORTATION EXCEL SUR-MESURE ---
    @admin.action(description="Exporter la sélection vers Excel (CSV)")
    def exporter_vers_excel(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Registre_Naissances.csv"'
        response.write('\ufeff'.encode('utf8')) 
        
        writer = csv.writer(response, delimiter=';')

        writer.writerow([
            'N° ACTE COMPLET', 'NOM DE L\'ENFANT', 'PRÉNOMS', 'DATE DE NAISSANCE', 
            'SEXE', 'NOM DU PÈRE', 'NATIONALITÉ PÈRE', 'NOM DE LA MÈRE', 'NATIONALITÉ MÈRE'
        ])

        for acte in queryset:
            if acte.date_declaration:
                date_decl_str = acte.date_declaration.strftime('%d/%m/%Y')
                numero_complet = f"{