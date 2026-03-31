from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Structure, ActeNaissance, CertificatResidence
import csv
import datetime
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Q, Case, When, Value, IntegerField

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
        # 1. Préparation du fichier
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Registre_Naissances.csv"'
        
        # ASTUCE DE PRO : On ajoute ça pour que Excel lise parfaitement les accents (é, à, ç)
        response.write('\ufeff'.encode('utf8')) 
        
        # On utilise le point-virgule car le tableur Excel en français l'exige pour séparer les colonnes
        writer = csv.writer(response, delimiter=';')

        # 2. Les titres de vos colonnes dans Excel
        writer.writerow([
            'N° ACTE COMPLET', 
            'NOM DE L\'ENFANT', 
            'PRÉNOMS', 
            'DATE DE NAISSANCE', 
            'SEXE',
            'NOM DU PÈRE',
            'NATIONALITÉ PÈRE',
            'NOM DE LA MÈRE',
            'NATIONALITÉ MÈRE'
        ])

        # 3. Remplissage avec les actes sélectionnés
        for acte in queryset:
            # Fabrication du Numéro Complet (ex: 01 du 12/01/2014)
            if acte.date_declaration:
                date_decl_str = acte.date_declaration.strftime('%d/%m/%Y')
                numero_complet = f"{acte.numero_registre} du {date_decl_str}"
            else:
                numero_complet = str(acte.numero_registre)

            # Écriture de la ligne dans Excel
            writer.writerow([
                numero_complet,
                acte.nom_enfant,
                acte.prenoms_enfant,
                acte.date_naissance.strftime('%d/%m/%Y') if acte.date_naissance else '',
                acte.sexe,
                acte.nom_pere,
                acte.nationalite_pere, # Vérifiez que ce champ s'appelle bien comme ça dans models.py
                acte.nom_mere,
                acte.nationalite_mere  # Vérifiez que ce champ s'appelle bien comme ça dans models.py
            ])

        return response

    # --- ENREGISTREMENT DE L'ACTION ---
    # Ajoutez cette ligne juste en dessous de la fonction pour faire apparaître le bouton
    actions = ['exporter_vers_excel']

  # --- 1. INTERCEPTEUR POUR ÉVITER LE CRASH DJANGO (?e=1) ---
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        custom_params = ['q_reference', 'q_nom', 'q_prenoms', 'q_date', 'q_mere']
        
        request.my_custom_search = {}
        mutable_get = request.GET.copy()
        
        for param in custom_params:
            val = request.GET.get(param, '')
            extra_context[param] = val
            request.my_custom_search[param] = val
            
            if param in mutable_get:
                del mutable_get[param]
                
        request.GET = mutable_get
        return super().changelist_view(request, extra_context=extra_context)

    # --- 2. LE MOTEUR DE RECHERCHE CLASSIQUE ET SÉCURISÉ ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        search_data = getattr(request, 'my_custom_search', {})
        q_reference = search_data.get('q_reference', '')
        q_nom = search_data.get('q_nom', '')
        q_prenoms = search_data.get('q_prenoms', '')
        q_date = search_data.get('q_date', '')
        q_mere = search_data.get('q_mere', '')

        # Si aucune recherche n'est lancée, on affiche tout (trié du plus récent au plus ancien)
        if not any([q_reference, q_nom, q_prenoms, q_date, q_mere]):
            return qs.order_by('-id')

        # --- FILTRAGE STRICT DE LA RECHERCHE ---
        if q_reference:
            q_reference = q_reference.strip().lower()
            if " du " in q_reference:
                morceaux = q_reference.split(" du ")
                num = morceaux[0].strip()
                date_str = morceaux[1].strip().replace('-', '/')
                
                nums = [num]
                if num.isdigit():
                    nums.append(str(int(num)))

                try:
                    date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y').date()
                    qs = qs.filter(numero_registre__in=nums).filter(Q(date_declaration=date_obj) | Q(date_naissance=date_obj))
                except ValueError:
                    qs = qs.filter(numero_registre__in=nums)
            else:
                qs = qs.filter(numero_registre__icontains=q_reference)
                
        if q_nom: qs = qs.filter(nom_enfant__icontains=q_nom) 
        if q_prenoms: qs = qs.filter(prenoms_enfant__icontains=q_prenoms)
        if q_date: qs = qs.filter(date_naissance=q_date)
        if q_mere: qs = qs.filter(nom_mere__icontains=q_mere)

        return qs.order_by('-id')

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

        # --- NOUVEAU : CALCUL DES STATISTIQUES DE NAISSANCE ---
        maintenant = timezone.now()
        annee_en_cours = maintenant.year
        mois_en_cours = maintenant.month

        # Calculs via la base de données
        total_naissances = ActeNaissance.objects.count()
        naissances_garcons = ActeNaissance.objects.filter(sexe='M').count()
        naissances_filles = ActeNaissance.objects.filter(sexe='F').count()
        naissances_annee = ActeNaissance.objects.filter(date_declaration__year=annee_en_cours).count()
        naissances_mois = ActeNaissance.objects.filter(date_declaration__year=annee_en_cours, date_declaration__month=mois_en_cours).count()

        # Envoi des résultats à la page web
        extra_context.update({
            'total_naissances': total_naissances,
            'naissances_garcons': naissances_garcons,
            'naissances_filles': naissances_filles,
            'naissances_annee': naissances_annee,
            'annee_en_cours': annee_en_cours, # <-- LA SEULE LIGNE À AJOUTER ICI
        })

        return super().index(request, extra_context=extra_context)
       
# Gardez la suite de vos enregistrements tels quels :
# custom_admin_site = CustomAdminSite(name='custom_admin')
# custom_admin_site.register(Structure) ...

custom_admin_site = CustomAdminSite(name='custom_admin')
custom_admin_site.register(Structure) 
custom_admin_site.register(ActeNaissance)