import os
import csv
import datetime
import qrcode
import base64
from io import BytesIO
from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.conf import settings
from django.utils.html import format_html
from django.template.loader import render_to_string

# --- IMPORTATION POUR LES UTILISATEURS ET MOTS DE PASSE ---
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

# --- IMPORTATION DE VOS MODÈLES ---
from .models import (
    Structure, ActeNaissance, CertificatResidence, 
    CertificatCelibat, CertificatNonDeces,
    CertificatNonDivorce, CertificatNonRemariage,
    CertificatNonSeparationCorps, CertificatVie,
    ActeMariage
)

# ==============================================================================
# 1. ADMINISTRATION DES ACTES DE NAISSANCE
# ==============================================================================
class ActeNaissanceAdmin(admin.ModelAdmin):
    list_display = ('numero_registre', 'nom_enfant', 'prenoms_enfant', 'date_naissance', 'sexe', 'date_declaration', 'boutons_impression')
    
    # --- ORGANISATION DES CHAMPS EN 3 BLOCS ---
    fieldsets = (
        ('1. L\'ENFANT ET LE REGISTRE', {
            'fields': (
                'structure', 'numero_registre', 'annee_registre', 'date_declaration',
                'nom_enfant', 'prenoms_enfant', 'sexe', 'date_naissance', 'heure_naissance', 'lieu_naissance',
                'transcription_justice', 'nom_sous_prefet'
            )
        }),
        ('2. FILIATION (PÈRE ET MÈRE)', {
            'description': 'Informations détaillées sur les parents de l\'enfant',
            'fields': (
                # Père
                'nom_pere', 'date_naissance_pere', 'profession_pere', 'domicile_pere', 'nationalite_pere',
                # Mère
                'nom_mere', 'date_naissance_mere', 'profession_mere', 'domicile_mere', 'nationalite_mere'
            )
        }),
        ('3. MENTIONS ÉVENTUELLES', {
            'classes': ('collapse',), # Le bloc reste replié pour plus de clarté
            'fields': (
                'date_mariage', 'conjoint_mariage', 'dissolution_mariage', 
                'date_deces', 'lieu_deces'
            )
        }),
    )

    # --- NOUVEAU : LES DEUX BOUTONS D'IMPRESSION ---
    def boutons_impression(self, obj):
        url_extrait = f"/extrait/{obj.id}/" 
        url_copie = f"/admin/acte_naissance/{obj.id}/copie_integrale/"
        return format_html(
            '<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold; margin-right: 5px;">🖨️ Extrait</a>'
            '<a href="{}" target="_blank" style="background: #28a745; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">📄 Copie Intégrale</a>',
            url_extrait, url_copie
        )
    boutons_impression.short_description = "Actions"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        custom_params = ['q_reference', 'q_nom', 'q_prenoms', 'q_date', 'q_mere']
        request.my_custom_search = {}
        mutable_get = request.GET.copy()
        for param in custom_params:
            val = request.GET.get(param, '')
            extra_context[param] = val
            request.my_custom_search[param] = val
            if param in mutable_get: del mutable_get[param]
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

        if not any([q_reference, q_nom, q_prenoms, q_date, q_mere]): return qs.order_by('-id')

        if q_reference:
            q_reference = q_reference.strip().lower()
            if " du " in q_reference:
                morceaux = q_reference.split(" du ")
                num = morceaux[0].strip()
                date_str = morceaux[1].strip().replace('-', '/')
                nums = [num, str(int(num)) if num.isdigit() else num]
                try:
                    date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y').date()
                    qs = qs.filter(numero_registre__in=nums).filter(Q(date_declaration=date_obj) | Q(date_naissance=date_obj))
                except ValueError: qs = qs.filter(numero_registre__in=nums)
            else: qs = qs.filter(numero_registre__icontains=q_reference)
        if q_nom: qs = qs.filter(nom_enfant__icontains=q_nom) 
        if q_prenoms: qs = qs.filter(prenoms_enfant__icontains=q_prenoms)
        if q_date: qs = qs.filter(date_naissance=q_date)
        if q_mere: qs = qs.filter(nom_mere__icontains=q_mere)
        return qs.order_by('-id')

    @admin.action(description="Exporter vers Excel (CSV)")
    def exporter_vers_excel(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Registre_Naissances.csv"'
        response.write('\ufeff'.encode('utf8')) 
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['N° ACTE COMPLET', 'NOM', 'PRÉNOMS', 'DATE NAISSANCE', 'SEXE', 'PÈRE', 'MÈRE'])
        for acte in queryset:
            date_str = acte.date_declaration.strftime('%d/%m/%Y') if acte.date_declaration else ''
            writer.writerow([f"{acte.numero_registre} du {date_str}", acte.nom_enfant, acte.prenoms_enfant, acte.date_naissance.strftime('%d/%m/%Y') if acte.date_naissance else '', acte.sexe, acte.nom_pere, acte.nom_mere])
        return response
    actions = ['exporter_vers_excel']

# ==============================================================================
# 2. ADMINISTRATION DES ACTES DE MARIAGE
# ==============================================================================
class ActeMariageAdmin(admin.ModelAdmin):
    list_display = ('numero_registre', 'nom_prenoms_epoux', 'nom_prenoms_epouse', 'date_mariage', 'bouton_imprimer')
    search_fields = ('numero_registre', 'nom_prenoms_epoux', 'nom_prenoms_epouse')

    fieldsets = (
        ('1. INFORMATIONS DU REGISTRE', {
            'fields': ('numero_registre', 'annee_registre', 'date_mariage', 'date_etablissement', 'nom_officier')
        }),
        ('2. L\'ÉPOUX (LE MARI)', {
            'fields': (
                'nom_prenoms_epoux', 'date_naissance_epoux', 'lieu_naissance_epoux', 'nationalite_epoux',
                'pere_epoux', 'nationalite_pere_epoux', 'mere_epoux', 'nationalite_mere_epoux', 'domicile_parents_epoux'
            )
        }),
        ('3. L\'ÉPOUSE (LA FEMME)', {
            'fields': (
                'nom_prenoms_epouse', 'date_naissance_epouse', 'lieu_naissance_epouse', 'nationalite_epouse',
                'pere_epouse', 'nationalite_pere_epouse', 'mere_epouse', 'nationalite_mere_epouse', 'domicile_parents_epouse'
            )
        }),
        ('4. MENTIONS MARGINALES', {
            'classes': ('collapse',),
            'fields': ('mentions_marginales',)
        }),
    )

    def bouton_imprimer(self, obj):
        url = f"/admin/acte_mariage/{obj.id}/imprimer/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', url)
    bouton_imprimer.short_description = "Action"

# ==============================================================================
# 3. ADMINISTRATION DES CERTIFICATS
# ==============================================================================
class CertificatCelibatAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer')
    search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj):
        url = f"/admin/certificat_celibat/{obj.id}/imprimer/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', url)

class CertificatNonDivorceAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer')
    search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj):
        url = f"/admin/certificat_non_divorce/{obj.id}/imprimer/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', url)

class CertificatNonRemariageAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer')
    search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj):
        url = f"/admin/certificat_non_remariage/{obj.id}/imprimer/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', url)

class CertificatNonSeparationCorpsAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer')
    search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj):
        url = f"/admin/certificat_non_separation/{obj.id}/imprimer/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', url)

class CertificatVieAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer')
    search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj):
        url = f"/admin/certificat_vie/{obj.id}/imprimer/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', url)

class CertificatResidenceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'bouton_imprimer') 
    def bouton_imprimer(self, obj):
        url = f"/certificat/{obj.id}/imprimer/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', url)

class CertificatNonDecesAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_defunt', 'date_etablissement', 'bouton_imprimer')
    search_fields = ('numero_certificat', 'nom_defunt')
    def bouton_imprimer(self, obj):
        url = f"/admin/certificat_non_deces/{obj.id}/imprimer/" 
        return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', url)

# ==============================================================================
# 4. CONFIGURATION DU TABLEAU DE BORD (CustomAdminSite)
# ==============================================================================
class CustomAdminSite(admin.AdminSite):
    site_header = "Administration de l'État Civil"
    site_title = "État Civil"
    index_title = "Tableau de Bord"

    def index(self, request, extra_context=None):
        structure = Structure.objects.first()
        extra_context = extra_context or {}
        extra_context.update({
            'structure': structure,
            'total_naissances': ActeNaissance.objects.count(),
            'total_mariages': ActeMariage.objects.count(),
            'naissances_annee': ActeNaissance.objects.filter(date_declaration__year=timezone.now().year).count(),
        })
        return super().index(request, extra_context=extra_context)

    def backup_database(self, request):
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        return FileResponse(open(db_path, 'rb'), as_attachment=True, filename=f'sauvegarde_etat_civil_{timezone.now().strftime("%d_%m_%Y")}.sqlite3')

    # --- MÉTHODE GÉNÉRIQUE POUR LES QR CODES ---
    def generer_qr_code(self, titre, numero, nom, date, sp):
        qr_data = f"{titre}\nN°: {numero}\nNoms: {nom}\nDate: {date}\nDélivré par: SP {sp}"
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(qr_data); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO(); img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    # --- IMPRESSIONS ---
    
    # NOUVEAU : IMPRESSION DE LA COPIE INTÉGRALE
    def imprimer_copie_integrale(self, request, pk):
        a = ActeNaissance.objects.get(pk=pk)
        s = Structure.objects.first()
        qr = self.generer_qr_code("COPIE INTÉGRALE", a.numero_registre, f"{a.nom_enfant} {a.prenoms_enfant}", timezone.now().strftime('%d/%m/%Y'), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/copie_integrale_print.html', {'a': a, 's': s, 'qr_base64': qr}))

    def imprimer_acte_mariage(self, request, pk):
        m, s = ActeMariage.objects.get(pk=pk), Structure.objects.first()
        noms_couple = f"{m.nom_prenoms_epoux} & {m.nom_prenoms_epouse}"
        qr = self.generer_qr_code("MARIAGE", m.numero_registre, noms_couple, m.date_etablissement.strftime('%d/%m/%Y'), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/acte_mariage_print.html', {'m': m, 's': s, 'qr_base64': qr}))

    def imprimer_registre_annuel(self, request):
        context = {'actes': ActeNaissance.objects.filter(date_declaration__year=timezone.now().year).order_by('numero_registre'), 'structure': Structure.objects.first()}
        return HttpResponse(render_to_string('registre/registre_annuel_print.html', context))

    def imprimer_certificat_celibat(self, request, pk):
        c, s = CertificatCelibat.objects.get(pk=pk), Structure.objects.first()
        qr = self.generer_qr_code("CÉLIBAT", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y'), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_celibat_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_non_divorce(self, request, pk):
        c, s = CertificatNonDivorce.objects.get(pk=pk), Structure.objects.first()
        qr = self.generer_qr_code("NON DIVORCE", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y'), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_non_divorce_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_non_remariage(self, request, pk):
        c, s = CertificatNonRemariage.objects.get(pk=pk), Structure.objects.first()
        qr = self.generer_qr_code("NON REMARIAGE", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y'), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_non_remariage_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_non_separation(self, request, pk):
        c, s = CertificatNonSeparationCorps.objects.get(pk=pk), Structure.objects.first()
        qr = self.generer_qr_code("NON SÉPARATION", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y'), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_non_separation_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_vie(self, request, pk):
        c, s = CertificatVie.objects.get(pk=pk), Structure.objects.first()
        qr = self.generer_qr_code("CERTIFICAT DE VIE", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y'), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_vie_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_non_deces(self, request, pk):
        c, s = CertificatNonDeces.objects.get(pk=pk), Structure.objects.first()
        qr_data = f"NON DÉCLARATION DÉCÈS\nN°: {c.numero_certificat}\nDéfunt: {c.nom_defunt}\nFait le: {c.date_etablissement.strftime('%d/%m/%Y')}"
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(qr_data); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO(); img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return HttpResponse(render_to_string('registre/certificat_non_deces_print.html', {'c': c, 's': s, 'qr_base64': qr_base64}))

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('backup-db/', self.admin_view(self.backup_database), name='backup_db'),
            path('print-registre/', self.admin_view(self.imprimer_registre_annuel), name='print_registre'),
            
            # --- NOUVELLE ROUTE POUR LA COPIE INTÉGRALE ---
            path('acte_naissance/<int:pk>/copie_integrale/', self.admin_view(self.imprimer_copie_integrale), name='print_copie_integrale'),
            
            path('acte_mariage/<int:pk>/imprimer/', self.admin_view(self.imprimer_acte_mariage), name='print_mariage'),
            path('certificat_celibat/<int:pk>/imprimer/', self.admin_view(self.imprimer_certificat_celibat), name='print_celibat'),
            path('certificat_non_divorce/<int:pk>/imprimer/', self.admin_view(self.imprimer_certificat_non_divorce), name='print_non_divorce'),
            path('certificat_non_remariage/<int:pk>/imprimer/', self.admin_view(self.imprimer_certificat_non_remariage), name='print_non_remariage'),
            path('certificat_non_separation/<int:pk>/imprimer/', self.admin_view(self.imprimer_certificat_non_separation), name='print_non_separation'),
            path('certificat_vie/<int:pk>/imprimer/', self.admin_view(self.imprimer_certificat_vie), name='print_vie'),
            path('certificat_non_deces/<int:pk>/imprimer/', self.admin_view(self.imprimer_certificat_non_deces), name='print_non_deces'),
        ]
        return custom_urls + urls

# ==============================================================================
# 5. ENREGISTREMENT FINAL
# ==============================================================================
custom_admin_site = CustomAdminSite(name='admin')
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Group, GroupAdmin)
custom_admin_site.register(Structure)
custom_admin_site.register(ActeNaissance, ActeNaissanceAdmin)
custom_admin_site.register(ActeMariage, ActeMariageAdmin)
custom_admin_site.register(CertificatResidence, CertificatResidenceAdmin)
custom_admin_site.register(CertificatCelibat, CertificatCelibatAdmin)
custom_admin_site.register(CertificatNonDivorce, CertificatNonDivorceAdmin)
custom_admin_site.register(CertificatNonRemariage, CertificatNonRemariageAdmin)
custom_admin_site.register(CertificatNonSeparationCorps, CertificatNonSeparationCorpsAdmin)
custom_admin_site.register(CertificatVie, CertificatVieAdmin)
custom_admin_site.register(CertificatNonDeces, CertificatNonDecesAdmin)