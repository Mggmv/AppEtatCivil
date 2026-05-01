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
from .models import Structure, ActeNaissance, CertificatResidence, CertificatCelibat, CertificatNonDeces 

# ==============================================================================
# 1. ADMINISTRATION DES ACTES DE NAISSANCE
# ==============================================================================
class ActeNaissanceAdmin(admin.ModelAdmin):
    list_display = ('numero_registre', 'nom_enfant', 'prenoms_enfant', 'date_naissance', 'sexe', 'date_declaration', 'bouton_imprimer')
    
    def bouton_imprimer(self, obj):
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
# 2. ADMINISTRATION DES CERTIFICATS
# ==============================================================================
class CertificatCelibatAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer')
    search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj):
        url = f"/admin/certificat_celibat/{obj.id}/imprimer/" 
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
# 3. CONFIGURATION DU TABLEAU DE BORD (CustomAdminSite)
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
            'naissances_annee': ActeNaissance.objects.filter(date_declaration__year=timezone.now().year).count(),
        })
        return super().index(request, extra_context=extra_context)

    def backup_database(self, request):
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        return FileResponse(open(db_path, 'rb'), as_attachment=True, filename=f'sauvegarde_etat_civil_{timezone.now().strftime("%d_%m_%Y")}.sqlite3')

    # --- IMPRESSIONS ---
    def imprimer_registre_annuel(self, request):
        context = {'actes': ActeNaissance.objects.filter(date_declaration__year=timezone.now().year).order_by('numero_registre'), 'structure': Structure.objects.first()}
        return HttpResponse(render_to_string('registre/registre_annuel_print.html', context))

    def imprimer_certificat_celibat(self, request, pk):
        c, s = CertificatCelibat.objects.get(pk=pk), Structure.objects.first()
        qr_data = f"CÉLIBAT\nN°: {c.numero_certificat}\nNom: {c.nom_prenoms}\nDate: {c.date_etablissement.strftime('%d/%m/%Y')}"
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(qr_data); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO(); img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return HttpResponse(render_to_string('registre/certificat_celibat_print.html', {'c': c, 's': s, 'qr_base64': qr_base64}))

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
            path('certificat_celibat/<int:pk>/imprimer/', self.admin_view(self.imprimer_certificat_celibat), name='print_celibat'),
            path('certificat_non_deces/<int:pk>/imprimer/', self.admin_view(self.imprimer_certificat_non_deces), name='print_non_deces'),
        ]
        return custom_urls + urls

# ==============================================================================
# 4. ENREGISTREMENT FINAL
# ==============================================================================
custom_admin_site = CustomAdminSite(name='admin')
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Group, GroupAdmin)
custom_admin_site.register(Structure)
custom_admin_site.register(ActeNaissance, ActeNaissanceAdmin)
custom_admin_site.register(CertificatResidence, CertificatResidenceAdmin)
custom_admin_site.register(CertificatCelibat, CertificatCelibatAdmin)
custom_admin_site.register(CertificatNonDeces, CertificatNonDecesAdmin)