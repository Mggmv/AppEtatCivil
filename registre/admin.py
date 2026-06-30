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

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from .models import (
    Structure, ActeNaissance, CertificatResidence, 
    CertificatCelibat, CertificatNonDeces,
    CertificatNonDivorce, CertificatNonRemariage,
    CertificatNonSeparationCorps, CertificatVie,
    ActeMariage
)

class ActeNaissanceAdmin(admin.ModelAdmin):
    # AFFICHAGE DES COLONNES (Avec "boutons_impression" à la fin)
    list_display = ('structure', 'numero_registre', 'nom_enfant', 'prenoms_enfant', 'date_naissance', 'sexe', 'date_declaration', 'boutons_impression')
    
    # FILTRES LATÉRAUX
    list_filter = ('structure', 'annee_registre', 'sexe')
    
    # ORGANISATION DU FORMULAIRE DE SAISIE
    fieldsets = (
        ('1. L\'ENFANT ET LE REGISTRE', {
            'fields': (
                'structure', 'numero_registre', 'annee_registre', 'date_declaration',
                'nom_enfant', 'prenoms_enfant', 'sexe', 'date_naissance', 'heure_naissance', 'lieu_naissance',
                'transcription_justice', 'nom_officier_creation', 'nom_sous_prefet'
            )
        }),
        ('2. FILIATION (PÈRE ET MÈRE)', {
            'description': 'Informations détaillées sur les parents de l\'enfant',
            'fields': (
                'nom_pere', 'date_naissance_pere', 'profession_pere', 'domicile_pere', 'nationalite_pere',
                'nom_mere', 'date_naissance_mere', 'profession_mere', 'domicile_mere', 'nationalite_mere'
            )
        }),
        ('3. MENTIONS ÉVENTUELLES', {
            'classes': ('collapse',),
            'fields': (
                'date_mariage', 'conjoint_mariage', 'dissolution_mariage', 
                'date_deces', 'lieu_deces'
            )
        }),
    )

    # FONCTION POUR AFFICHER LES BOUTONS D'IMPRESSION DANS LE TABLEAU
    def boutons_impression(self, obj):
        url_extrait = f"/extrait/{obj.id}/" 
        url_copie = f"/admin/acte_naissance/{obj.id}/copie_integrale/"
        return format_html(
            '<div style="display: flex; gap: 5px; flex-wrap: wrap; justify-content: flex-start;">'
            '<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 11px; font-weight: bold; white-space: nowrap;">🖨️ Extrait</a>'
            '<a href="{}" target="_blank" style="background: #28a745; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 11px; font-weight: bold; white-space: nowrap;">📄 Copie Intégrale</a>'
            '</div>',
            url_extrait, url_copie
        )
    boutons_impression.short_description = "Actions"

    # INTERCEPTION DE LA VUE LISTE POUR LES BARRES DE RECHERCHE PERSONNALISÉES
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

    # APPLICATION DES FILTRES DE RECHERCHE PERSONNALISÉS
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        search_data = getattr(request, 'my_custom_search', {})
        q_reference = search_data.get('q_reference', '')
        q_nom = search_data.get('q_nom', '')
        q_prenoms = search_data.get('q_prenoms', '')
        q_date = search_data.get('q_date', '')
        q_mere = search_data.get('q_mere', '')

        # Si aucune recherche, on renvoie tout, classé du plus récent au plus ancien
        if not any([q_reference, q_nom, q_prenoms, q_date, q_mere]): 
            return qs.order_by('-id')

        # Recherche par référence intelligente (ex: "23 du 12/04/2005")
        if q_reference:
            q_reference = q_reference.strip().lower()
            if " du " in q_reference:
                morceaux = q_reference.split(" du ")
                num = morceaux[0].strip()
                date_str = morceaux[1].strip().replace('-', '/')
                nums = [num, str(int(num)) if num.isdigit() else num]
                try:
                    date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y').date()
                    qs = qs.filter(numero_registre__in=nums).filter(Q(date_declaration=date_obj) | Q(date_naissance__icontains=date_str))
                except ValueError: 
                    qs = qs.filter(numero_registre__in=nums)
            else: 
                qs = qs.filter(numero_registre__icontains=q_reference)
                
        # Recherches par identité
        if q_nom: qs = qs.filter(nom_enfant__icontains=q_nom) 
        if q_prenoms: qs = qs.filter(prenoms_enfant__icontains=q_prenoms)
        if q_date: qs = qs.filter(date_naissance__icontains=q_date)
        if q_mere: qs = qs.filter(nom_mere__icontains=q_mere)
        
        return qs.order_by('-id')

    # ACTION PERSONNALISÉE : EXPORTATION EXCEL
    @admin.action(description="Exporter vers Excel (CSV Complet)")
    def exporter_vers_excel(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Registre_Naissances_Complet.csv"'
        response.write('\ufeff'.encode('utf8')) 
        writer = csv.writer(response, delimiter=';')
        
        # En-têtes du fichier CSV
        writer.writerow([
            'N° ACTE', 'ANNÉE REGISTRE', 'DATE DÉCLARATION', 'CENTRE ÉTAT CIVIL',
            'NOM', 'PRÉNOMS', 'SEXE', 'DATE NAISSANCE', 'HEURE NAISSANCE', 'LIEU NAISSANCE',
            'NOM PÈRE', 'DATE NAISSANCE PÈRE', 'PROFESSION PÈRE', 'DOMICILE PÈRE', 'NATIONALITÉ PÈRE',
            'NOM MÈRE', 'DATE NAISSANCE MÈRE', 'PROFESSION MÈRE', 'DOMICILE MÈRE', 'NATIONALITÉ MÈRE',
            'DATE MARIAGE', 'CONJOINT(E)', 'DISSOLUTION MARIAGE',
            'DATE DÉCÈS', 'LIEU DÉCÈS', 'TRANSCRIPTION JUSTICE', 'OFFICIER ÉTAT CIVIL', 'OFFICIER CRÉATION'
        ])
        
        # Fonction de sécurité pour éviter le texte "None"
        def v(val):
            return val if val and str(val).strip().lower() != 'none' else ''

        for acte in queryset:
            # Sécurisation des formats de date et d'heure
            if acte.date_declaration:
                if hasattr(acte.date_declaration, 'strftime'):
                    date_dec_str = acte.date_declaration.strftime('%d/%m/%Y')
                else:
                    date_dec_str = str(acte.date_declaration)
            else:
                date_dec_str = ''
                
            if acte.heure_naissance:
                if hasattr(acte.heure_naissance, 'strftime'):
                    heure_str = acte.heure_naissance.strftime('%H:%M')
                else:
                    heure_str = str(acte.heure_naissance)
            else:
                heure_str = ''
                
            centre_str = acte.structure.nom_centre if hasattr(acte, 'structure') and acte.structure else ''

            # Écriture de la ligne pour chaque acte
            writer.writerow([
                v(acte.numero_registre), v(acte.annee_registre), v(date_dec_str), v(centre_str),
                v(acte.nom_enfant), v(acte.prenoms_enfant), v(acte.sexe), v(acte.date_naissance), v(heure_str), v(acte.lieu_naissance),
                v(acte.nom_pere), v(acte.date_naissance_pere), v(acte.profession_pere), v(acte.domicile_pere), v(acte.nationalite_pere),
                v(acte.nom_mere), v(acte.date_naissance_mere), v(acte.profession_mere), v(acte.domicile_mere), v(acte.nationalite_mere),
                v(acte.date_mariage), v(acte.conjoint_mariage), v(acte.dissolution_mariage),
                v(acte.date_deces), v(acte.lieu_deces), v(acte.transcription_justice), v(acte.nom_sous_prefet), v(acte.nom_officier_creation)
            ])
            
        return response

    actions = ['exporter_vers_excel']

class ActeMariageAdmin(admin.ModelAdmin):
    list_display = ('numero_registre', 'nom_prenoms_epoux', 'nom_prenoms_epouse', 'date_mariage', 'bouton_imprimer')
    search_fields = ('numero_registre', 'nom_prenoms_epoux', 'nom_prenoms_epouse')
    fieldsets = (
        ('1. INFORMATIONS DU REGISTRE', {'fields': ('numero_registre', 'annee_registre', 'date_mariage', 'date_etablissement', 'nom_officier')}),
        ('2. L\'ÉPOUX (LE MARI)', {'fields': ('nom_prenoms_epoux', 'date_naissance_epoux', 'lieu_naissance_epoux', 'nationalite_epoux', 'pere_epoux', 'nationalite_pere_epoux', 'mere_epoux', 'nationalite_mere_epoux', 'domicile_parents_epoux')}),
        ('3. L\'ÉPOUSE (LA FEMME)', {'fields': ('nom_prenoms_epouse', 'date_naissance_epouse', 'lieu_naissance_epouse', 'nationalite_epouse', 'pere_epouse', 'nationalite_pere_epouse', 'mere_epouse', 'nationalite_mere_epouse', 'domicile_parents_epouse')}),
        ('4. MENTIONS MARGINALES', {'classes': ('collapse',), 'fields': ('mentions_marginales',)}),
    )
    def bouton_imprimer(self, obj): return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', f"/admin/acte_mariage/{obj.id}/imprimer/")


class CertificatCelibatAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer'); search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj): return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', f"/admin/certificat_celibat/{obj.id}/imprimer/")
class CertificatNonDivorceAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer'); search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj): return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', f"/admin/certificat_non_divorce/{obj.id}/imprimer/")
class CertificatNonRemariageAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer'); search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj): return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', f"/admin/certificat_non_remariage/{obj.id}/imprimer/")
class CertificatNonSeparationCorpsAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer'); search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj): return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', f"/admin/certificat_non_separation/{obj.id}/imprimer/")
class CertificatVieAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_prenoms', 'date_etablissement', 'bouton_imprimer'); search_fields = ('numero_certificat', 'nom_prenoms')
    def bouton_imprimer(self, obj): return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', f"/admin/certificat_vie/{obj.id}/imprimer/")
class CertificatResidenceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'bouton_imprimer') 
    def bouton_imprimer(self, obj): return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', f"/certificat/{obj.id}/imprimer/")
class CertificatNonDecesAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'nom_defunt', 'date_etablissement', 'bouton_imprimer'); search_fields = ('numero_certificat', 'nom_defunt')
    def bouton_imprimer(self, obj): return format_html('<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">🖨️ Imprimer</a>', f"/admin/certificat_non_deces/{obj.id}/imprimer/")


class CustomAdminSite(admin.AdminSite):
    site_header = "Administration de l'État Civil"
    site_title = "État Civil"
    index_title = "Tableau de Bord Central"

    def index(self, request, extra_context=None):
        structure = Structure.objects.first()
        
        # NOUVEAUTÉ : On envoie la liste des années vers le Tableau de bord central !
        annees_brutes = ActeNaissance.objects.values_list('annee_registre', flat=True).distinct().order_by('-annee_registre')
        annees_disponibles = [a for a in annees_brutes if a and str(a).strip() != '']
        
        extra_context = extra_context or {}
        extra_context.update({
            'structure': structure,
            'total_naissances': ActeNaissance.objects.count(),
            'total_mariages': ActeMariage.objects.count(),
            'naissances_annee': ActeNaissance.objects.filter(date_declaration__year=timezone.now().year).count() if hasattr(ActeNaissance, 'date_declaration__year') else 0,
            'annees_disponibles': annees_disponibles,
        })
        return super().index(request, extra_context=extra_context)

    def backup_database(self, request):
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        return FileResponse(open(db_path, 'rb'), as_attachment=True, filename=f'sauvegarde_etat_civil_{timezone.now().strftime("%d_%m_%Y")}.sqlite3')

    def generer_qr_code(self, titre, numero, nom, date, sp):
        qr_data = f"{titre}\nN°: {numero}\nNoms: {nom}\nDate: {date}\nDélivré par: SP {sp}"
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(qr_data); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO(); img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def importer_naissances(self, request):
        from django.shortcuts import render, redirect
        from django.contrib import messages
        import csv, io, datetime
        if request.method == "POST":
            csv_file = request.FILES.get('csv_file')
            if not csv_file or not csv_file.name.endswith('.csv'):
                messages.error(request, "Fichier invalide."); return redirect('admin:import_naissances')
            try:
                decoded_file = csv_file.read().decode('utf-8-sig'); reader = csv.reader(io.StringIO(decoded_file), delimiter=';')
                try: header = next(reader) 
                except StopIteration: messages.error(request, "Fichier vide."); return redirect('admin:import_naissances')
                compteur_ajouts = 0; compteur_doublons = 0; is_old_format = len(header) < 15
                def parse_date(d_str):
                    if not d_str: return None
                    d_str = str(d_str).strip()
                    try: return datetime.datetime.strptime(d_str, '%d/%m/%Y').date()
                    except:
                        try: return datetime.datetime.strptime(d_str, '%Y-%m-%d').date()
                        except: return None
                def parse_time(t_str):
                    if not t_str: return None
                    t_str = str(t_str).strip()
                    try: return datetime.datetime.strptime(t_str, '%H:%M').time()
                    except: return None
                for row in reader:
                    if len(row) < 4: continue 
                    if is_old_format:
                        numero = row[0].strip(); date_dec = parse_date(row[1]) if len(row) > 1 else None
                        annee = str(date_dec.year) if date_dec else str(timezone.now().year)
                        if " du " in numero.lower(): numero = numero.lower().split(" du ")[0].strip()
                        structure, _ = Structure.objects.get_or_create(nom_centre="CENTRE INCONNU", defaults={'region': 'À DÉFINIR', 'prefecture': 'À DÉFINIR', 'sous_prefecture': "CENTRE INCONNU"})
                        if ActeNaissance.objects.filter(numero_registre=numero, annee_registre=annee, structure=structure).exists(): compteur_doublons += 1; continue
                        ActeNaissance.objects.create(numero_registre=numero, annee_registre=annee, date_declaration=date_dec, structure=structure, sexe=row[2].strip() if len(row)>2 else 'M', nom_enfant=row[3].strip() if len(row)>3 else '', prenoms_enfant=row[4].strip() if len(row)>4 else '', lieu_naissance=row[5].strip() if len(row)>5 else '', nom_pere=row[6].strip() if len(row)>6 else '', nom_mere=row[7].strip() if len(row)>7 else '')
                        compteur_ajouts += 1
                    else:
                        if len(row) < 26: continue
                        numero = row[0].strip(); annee = row[1].strip(); structure, _ = Structure.objects.get_or_create(nom_centre=row[3].strip(), defaults={'region': 'À DÉFINIR', 'prefecture': 'À DÉFINIR', 'sous_prefecture': row[3].strip()})
                        if ActeNaissance.objects.filter(numero_registre=numero, annee_registre=annee, structure=structure).exists(): compteur_doublons += 1; continue
                        ActeNaissance.objects.create(numero_registre=numero, annee_registre=annee, date_declaration=parse_date(row[2]), structure=structure, nom_enfant=row[4], prenoms_enfant=row[5], sexe=row[6], date_naissance=row[7], heure_naissance=parse_time(row[8]), lieu_naissance=row[9], nom_pere=row[10], date_naissance_pere=row[11], profession_pere=row[12], domicile_pere=row[13], nationalite_pere=row[14], nom_mere=row[15], date_naissance_mere=row[16], profession_mere=row[17], domicile_mere=row[18], nationalite_mere=row[19], date_mariage=row[20], conjoint_mariage=row[21], dissolution_mariage=row[22], date_deces=row[23], lieu_deces=row[24], transcription_justice=row[25], nom_sous_prefet=row[26] if len(row) > 26 else "", nom_officier_creation=row[27] if len(row) > 27 else "")
                        compteur_ajouts += 1
                messages.success(request, f"IMPORTATION TERMINÉE : {compteur_ajouts} ajoutés, {compteur_doublons} ignorés."); return redirect('admin:registre_actenaissance_changelist')
            except Exception as e: messages.error(request, f"Erreur : {str(e)}"); return redirect('admin:import_naissances')
        return render(request, 'admin/import_csv.html')

    def imprimer_copie_integrale(self, request, pk):
        a = ActeNaissance.objects.get(pk=pk); s = Structure.objects.first()
        qr = self.generer_qr_code("COPIE INTÉGRALE", a.numero_registre, f"{a.nom_enfant} {a.prenoms_enfant}" if a.prenoms_enfant else f"{a.nom_enfant}", timezone.now().strftime('%d/%m/%Y'), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/copie_integrale_print.html', {'a': a, 's': s, 'qr_base64': qr}))

    def imprimer_acte_mariage(self, request, pk):
        m = ActeMariage.objects.get(pk=pk); s = Structure.objects.first()
        qr = self.generer_qr_code("MARIAGE", m.numero_registre, f"{m.nom_prenoms_epoux} & {m.nom_prenoms_epouse}", m.date_etablissement.strftime('%d/%m/%Y'), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/acte_mariage_print.html', {'m': m, 's': s, 'qr_base64': qr}))

    def imprimer_registre_annuel(self, request):
        annee = request.GET.get('annee')
        if not annee: annee = str(timezone.now().year)
        actes = ActeNaissance.objects.filter(annee_registre=annee).order_by('numero_registre')
        return HttpResponse(render_to_string('registre/registre_annuel_print.html', {'actes': actes, 'structure': Structure.objects.first(), 'annee': annee, 'total': actes.count(), 'date_edition': timezone.now()}))

    def imprimer_certificat_celibat(self, request, pk):
        c = CertificatCelibat.objects.get(pk=pk); s = Structure.objects.first()
        qr = self.generer_qr_code("CÉLIBAT", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y') if hasattr(c.date_etablissement, 'strftime') else str(c.date_etablissement), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_celibat_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_non_divorce(self, request, pk):
        c = CertificatNonDivorce.objects.get(pk=pk); s = Structure.objects.first()
        qr = self.generer_qr_code("NON DIVORCE", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y') if hasattr(c.date_etablissement, 'strftime') else str(c.date_etablissement), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_non_divorce_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_non_remariage(self, request, pk):
        c = CertificatNonRemariage.objects.get(pk=pk); s = Structure.objects.first()
        qr = self.generer_qr_code("NON REMARIAGE", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y') if hasattr(c.date_etablissement, 'strftime') else str(c.date_etablissement), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_non_remariage_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_non_separation(self, request, pk):
        c = CertificatNonSeparationCorps.objects.get(pk=pk); s = Structure.objects.first()
        qr = self.generer_qr_code("NON SÉPARATION", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y') if hasattr(c.date_etablissement, 'strftime') else str(c.date_etablissement), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_non_separation_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_vie(self, request, pk):
        c = CertificatVie.objects.get(pk=pk); s = Structure.objects.first()
        qr = self.generer_qr_code("CERTIFICAT DE VIE", c.numero_certificat, c.nom_prenoms, c.date_etablissement.strftime('%d/%m/%Y') if hasattr(c.date_etablissement, 'strftime') else str(c.date_etablissement), s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_vie_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def imprimer_certificat_non_deces(self, request, pk):
        c = CertificatNonDeces.objects.get(pk=pk); s = Structure.objects.first()
        date_estab = c.date_etablissement.strftime('%d/%m/%Y') if hasattr(c.date_etablissement, 'strftime') else str(c.date_etablissement)
        qr = self.generer_qr_code("NON DÉCLARATION DÉCÈS", c.numero_certificat, c.nom_defunt, date_estab, s.sous_prefecture if s else '')
        return HttpResponse(render_to_string('registre/certificat_non_deces_print.html', {'c': c, 's': s, 'qr_base64': qr}))

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('importer-naissances/', self.admin_view(self.importer_naissances), name='import_naissances'),
            path('backup-db/', self.admin_view(self.backup_database), name='backup_db'),
            path('print-registre/', self.admin_view(self.imprimer_registre_annuel), name='print_registre'),
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

custom_admin_site = CustomAdminSite(name='admin')
custom_admin_site.register(User, UserAdmin); custom_admin_site.register(Group, GroupAdmin); custom_admin_site.register(Structure)
custom_admin_site.register(ActeNaissance, ActeNaissanceAdmin); custom_admin_site.register(ActeMariage, ActeMariageAdmin)
custom_admin_site.register(CertificatResidence, CertificatResidenceAdmin); custom_admin_site.register(CertificatCelibat, CertificatCelibatAdmin)
custom_admin_site.register(CertificatNonDivorce, CertificatNonDivorceAdmin); custom_admin_site.register(CertificatNonRemariage, CertificatNonRemariageAdmin)
custom_admin_site.register(CertificatNonSeparationCorps, CertificatNonSeparationCorpsAdmin); custom_admin_site.register(CertificatVie, CertificatVieAdmin)
custom_admin_site.register(CertificatNonDeces, CertificatNonDecesAdmin)
