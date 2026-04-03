import os
import csv
import datetime
from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.conf import settings
from django.utils.html import format_html

# --- IMPORTATION POUR LES UTILISATEURS ET MOTS DE PASSE ---
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

# --- IMPORTATION DE VOS MODÈLES ---
from .models import Structure, ActeNaissance, CertificatResidence 

# ==============================================================================
# 1. ADMINISTRATION DES ACTES DE NAISSANCE
# ==============================================================================
class ActeNaissanceAdmin(admin.ModelAdmin):
    # Les colonnes affichées dans le tableau (avec le bouton imprimer à la fin)
    list_display = ('numero_registre', 'nom_enfant', 'prenoms_enfant', 'date_naissance', 'sexe', 'date_declaration', 'bouton_imprimer')
    
    # --- BOUTON IMPRIMER L'ACTE ---
    def bouton_imprimer(self, obj):
        # L'adresse a été corrigée grâce à votre capture d'écran !
        url = f"/extrait/{obj.id}/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold; white-space: nowrap;">🖨️ Imprimer</a>', url)
    bouton_imprimer.short_description = "Action"

    # --- LE MOTEUR DE RECHERCHE ---
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        search_data = getattr(request, 'my_custom_search', {})
        q_reference = search_data.get('q_reference', '')
        q_nom = search_data.get('q_nom', '')
        q_prenoms = search_data.get('q_prenoms', '')
        q_date = search_data.get('q_date', '')
        q_mere = search_data.get('q_mere', '')

        if not any([q_reference, q_nom, q_prenoms, q_date, q_mere]):
            return qs.order_by('-id')

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

    # --- L'EXPORT EXCEL ---
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
                numero_complet = f"{acte.numero_registre} du {date_decl_str}"
            else:
                numero_complet = str(acte.numero_registre)

            writer.writerow([
                numero_complet, acte.nom_enfant, acte.prenoms_enfant,
                acte.date_naissance.strftime('%d/%m/%Y') if acte.date_naissance else '',
                acte.sexe, acte.nom_pere, acte.nationalite_pere,
                acte.nom_mere, acte.nationalite_mere
            ])

        return response
    actions = ['exporter_vers_excel']

# ==============================================================================
# 2. ADMINISTRATION DES CERTIFICATS DE RÉSIDENCE
# ==============================================================================
class CertificatResidenceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'bouton_imprimer') 

    # --- BOUTON IMPRIMER LE CERTIFICAT ---
    def bouton_imprimer(self, obj):
        # L'adresse a été corrigée grâce à votre capture d'écran !
        url = f"/certificat/{obj.id}/imprimer/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold; white-space: nowrap;">🖨️ Imprimer</a>', url)
    bouton_imprimer.short_description = "Action"

# ==============================================================================
# 3. CONFIGURATION DU TABLEAU DE BORD GÉNÉRAL (CustomAdminSite)
# ==============================================================================
class CustomAdminSite(admin.AdminSite):
    site_header = "Administration de l'État Civil"
    site_title = "État Civil"
    index_title = "Tableau de Bord"

    def index(self, request, extra_context=None):
        structure = Structure.objects.first()
        extra_context = extra_context or {}
        extra_context['structure'] = structure

        maintenant = timezone.now()
        annee_en_cours = maintenant.year
        mois_en_cours = maintenant.month

        total_naissances = ActeNaissance.objects.count()
        naissances_garcons = ActeNaissance.objects.filter(sexe='M').count()
        naissances_filles = ActeNaissance.objects.filter(sexe='F').count()
        naissances_annee = ActeNaissance.objects.filter(date_declaration__year=annee_en_cours).count()

        extra_context.update({
            'total_naissances': total_naissances,
            'naissances_garcons': naissances_garcons,
            'naissances_filles': naissances_filles,
            'naissances_annee': naissances_annee,
            'annee_en_cours': annee_en_cours,
        })

        return super().index(request, extra_context=extra_context)

    def backup_database(self, request):
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        if os.path.exists(db_path):
            date_str = timezone.now().strftime('%d_%m_%Y')
            return FileResponse(open(db_path, 'rb'), as_attachment=True, filename=f'sauvegarde_etat_civil_{date_str}.sqlite3')
        return HttpResponse("Fichier de base de données introuvable.", status=404)

    def imprimer_registre_annuel(self, request):
        annee = timezone.now().year
        actes = ActeNaissance.objects.filter(date_declaration__year=annee).order_by('numero_registre')
        structure = Structure.objects.first()
        
        context = {
            'actes': actes,
            'annee': annee,
            'structure': structure,
            'total': actes.count(),
            'date_edition': timezone.now(),
        }
        from django.template.loader import render_to_string
        html_content = render_to_string('registre/registre_annuel_print.html', context)
        return HttpResponse(html_content)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        
        custom_urls = [
            path('backup-db/', self.admin_view(self.backup_database), name='backup_db'),
            path('print-registre/', self.admin_view(self.imprimer_registre_annuel), name='print_registre'),
        ]
        
        return custom_urls + urls

# ==============================================================================
# 4. ENREGISTREMENT DANS NOTRE INTERFACE PERSONNALISÉE
# ==============================================================================
custom_admin_site = CustomAdminSite(name='admin')

# 1. On réenregistre les Utilisateurs et les Groupes (Pour ne pas perdre vos accès)
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Group, GroupAdmin)

# 2. On enregistre les modèles de l'État Civil
custom_admin_site.register(Structure)
custom_admin_site.register(ActeNaissance, ActeNaissanceAdmin)
custom_admin_site.register(CertificatResidence, CertificatResidenceAdmin)