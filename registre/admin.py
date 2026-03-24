from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Structure, ActeNaissance, CertificatResidence
import csv
import datetime
from django.http import HttpResponse

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

    # --- ACTION : EXPORT EXCEL --- 
    @admin.action(description="📊 Exporter les actes sélectionnés en Excel")
    def exporter_en_excel(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="Registre_Etat_Civil.csv"'
        writer = csv.writer(response, delimiter=';')

        writer.writerow([
            'Numéro Acte', 'Date de Déclaration', 'Sexe', 'Nom', 'Prénoms', 
            'Lieu de Naissance', 'Nom du Père', 'Nom de la Mère'
        ])

        for acte in queryset:
            date_dec = acte.date_declaration.strftime('%d/%m/%Y') if acte.date_declaration else ''
            sexe_display = "Féminin" if acte.sexe == 'F' else "Masculin"

            writer.writerow([
                acte.numero_registre,
                date_dec,
                sexe_display,
                acte.nom_enfant.upper() if acte.nom_enfant else '',
                acte.prenoms_enfant,
                acte.lieu_naissance,
                acte.nom_pere if acte.nom_pere else 'Inconnu',
                acte.nom_mere if acte.nom_mere else 'Inconnue'
            ])
        return response

    actions = [exporter_en_excel]

    # --- LE MOTEUR DE RECHERCHE PERSONNALISÉ ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        q_reference = request.GET.get('q_reference')
        q_nom = request.GET.get('q_nom')
        q_prenoms = request.GET.get('q_prenoms')
        q_date = request.GET.get('q_date')
        q_mere = request.GET.get('q_mere')

        if q_reference:
            q_reference = q_reference.strip().lower()
            if " du " in q_reference:
                morceaux = q_reference.split(" du ")
                num = morceaux[0].strip()
                date_str = morceaux[1].strip().replace('-', '/')
                try:
                    date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y').date()
                    qs = qs.filter(numero_registre=num, date_naissance=date_obj)
                except ValueError:
                    qs = qs.filter(numero_registre__icontains=num)
            else:
                qs = qs.filter(numero_registre__icontains=q_reference)
                
        if q_nom: qs = qs.filter(nom_enfant__icontains=q_nom) 
        if q_prenoms: qs = qs.filter(prenoms_enfant__icontains=q_prenoms)
        if q_date: qs = qs.filter(date_naissance=q_date)
        if q_mere: qs = qs.filter(nom_mere__icontains=q_mere)

        return qs

# ==========================================
# 2. GESTION DES CERTIFICATS DE RÉSIDENCE
# ==========================================
@admin.register(CertificatResidence)
class CertificatResidenceAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom', 'prenoms', 'nationalite', 'date_etablissement', 'bouton_imprimer')
    search_fields = ('numero_certificat', 'nom', 'prenoms', 'nationalite')
    list_filter = ('date_etablissement', 'nationalite', 'sexe')
    
    fieldsets = (
        ('1. Références', {'fields': ('numero_certificat', 'date_etablissement')}),
        ('2. Identité du Demandeur', {'fields': ('nom', 'prenoms', 'sexe', 'date_naissance', 'lieu_naissance', 'nationalite', 'profession')}),
        ('3. Filiation', {'fields': ('nom_pere', 'nom_mere')}),
        ('4. Pièces et Résidence', {'fields': ('piece_identite', 'adresse_locale', 'resident_depuis')}),
    )

    def bouton_imprimer(self, obj):
        url = reverse('imprimer_certificat', args=[obj.id])
        return format_html(
            '<a class="button" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-weight: bold;" href="{}" target="_blank">🖨️ Imprimer</a>', 
            url
        )
    bouton_imprimer.short_description = "Action"
    bouton_imprimer.allow_tags = True

# ==========================================
# 3. PERSONNALISATION GLOBALE DU SITE
# ==========================================
class CustomAdminSite(admin.AdminSite):
    site_header = "Administration"

    def index(self, request, extra_context=None):
        structure = Structure.objects.first()
        extra_context = extra_context or {}
        extra_context['structure'] = structure
        return super().index(request, extra_context=extra_context)

custom_admin_site = CustomAdminSite(name='custom_admin')
custom_admin_site.register(Structure)
custom_admin_site.register(ActeNaissance)