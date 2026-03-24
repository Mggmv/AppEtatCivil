from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ActeNaissance
from .models import CertificatResidence, Structure

# --- Imports pour le QR Code ---
import qrcode
import base64
from io import BytesIO

# --- Imports pour l'export EXCEL ---
import csv
from django.http import HttpResponse

def home(request):
    return render(request, 'registre/home.html')

@login_required
def dashboard(request):
    actes = ActeNaissance.objects.all().order_by('-date_declaration')
    return render(request, 'registre/dashboard.html', {'actes': actes})

@login_required
def voir_extrait(request, pk):
    acte = get_object_or_404(ActeNaissance, pk=pk)
    
    # --- Date et Heure en lettres ---
    date_lettres = acte.infos_naissance_lettres()
    
    # ==========================================
    # --- BOUCLIER DE TRADUCTION (PyInstaller) ---
    # ==========================================
    traductions_mois = {
        "January": "janvier", "February": "février", "March": "mars", 
        "April": "avril", "May": "mai", "June": "juin", 
        "July": "juillet", "August": "août", "September": "septembre", 
        "October": "octobre", "November": "novembre", "December": "décembre"
    }
    for en, fr in traductions_mois.items():
        date_lettres = date_lettres.replace(en, fr)
        date_lettres = date_lettres.replace(en.lower(), fr)
        
    date_lettres = date_lettres.replace("mille", "mil")
    if date_lettres.startswith("un "):
        date_lettres = date_lettres.replace("un ", "premier ", 1)
    # ==========================================

    phrase_naissance = f"Le {date_lettres}"
    
    if acte.heure_naissance:
        h = acte.heure_naissance.hour
        m = acte.heure_naissance.minute
        conv = {
            0: "zéro", 1: "une", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq",
            6: "six", 7: "sept", 8: "huit", 9: "neuf", 10: "dix",
            11: "onze", 12: "douze", 13: "treize", 14: "quatorze", 15: "quinze",
            16: "seize", 17: "dix-sept", 18: "dix-huit", 19: "dix-neuf", 20: "vingt",
            21: "vingt et une", 22: "vingt-deux", 23: "vingt-trois", 30: "trente",
            40: "quarante", 50: "cinquante"
        }
        txt_h = conv.get(h, str(h)) + (" heure" if h <= 1 else " heures")
        txt_m = ""
        if m > 0:
            if m <= 20 or m in [30, 40, 50]:
                txt_m = " " + conv.get(m)
            else:
                d, u = divmod(m, 10)
                txt_m = f" {conv.get(d*10)}{' et ' if u == 1 else '-'}{conv.get(u)}"
        phrase_naissance += f" à {txt_h}{txt_m}"

    # ==========================================
    # --- GESTION DU SEXE ET DE LA GRAMMAIRE ---
    # ==========================================
    # Récupération sécurisée du sexe (par défaut 'M' si le champ n'est pas encore créé)
    sexe_enfant = getattr(acte, 'sexe', 'M')
    
    enfant_label = "Fille de " if sexe_enfant == 'F' else "Fils de "
    accord_ne = "née" if sexe_enfant == 'F' else "né"

    # --- Filiation (Père et Mère) ---
    if acte.nom_pere:
        pere_info = acte.nom_pere
        if getattr(acte, 'nationalite_pere', None):
            pere_info += f" de nationalité {acte.nationalite_pere}"
        pere_label = enfant_label
    else:
        pere_info = "de père inconnu"
        pere_label = ""

    if acte.nom_mere:
        mere_info = acte.nom_mere
        if getattr(acte, 'nationalite_mere', None):
            mere_info += f" de nationalité {acte.nationalite_mere}"
        mere_label = "et de "
    else:
        mere_info = "de mère inconnue"
        mere_label = "et "

    # ==========================================
    # --- GÉNÉRATION DU QR CODE HORS-LIGNE ---
    # ==========================================
    date_str = acte.date_declaration.strftime('%d/%m/%Y') if acte.date_declaration else ""
    qr_data = f"SOUS-PREFECTURE DE {acte.structure.sous_prefecture}\nACTE N: {acte.numero_registre} DU {date_str}\nNOM: {acte.nom_enfant}\nPRENOMS: {acte.prenoms_enfant}\nSEXE: {sexe_enfant}".upper()
    
    qr = qrcode.QRCode(version=1, box_size=4, border=0)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    # ==========================================

    context = {
        'acte': acte,
        'date_heure_complete': phrase_naissance,
        'pere_info': pere_info,
        'pere_label': pere_label,
        'mere_info': mere_info,
        'mere_label': mere_label,
        'qr_base64': qr_base64,
        'accord_ne': accord_ne, # On envoie "né" ou "née" au HTML
    }
    return render(request, 'registre/extrait_naissance.html', context)

# ==========================================
# --- FONCTION : EXPORT EXCEL ---
# ==========================================
@login_required
def exporter_actes_csv(request):
    # Prépare le fichier avec l'encodage 'utf-8-sig' pour qu'Excel lise bien les accents
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="Registre_Etat_Civil_2026.csv"'

    writer = csv.writer(response, delimiter=';')

    # Ligne 1 : Les en-têtes des colonnes avec le Sexe ajouté !
    writer.writerow([
        'Numéro Acte', 'Date de Déclaration', 'Sexe', 'Nom', 'Prénoms', 
        'Lieu de Naissance', 'Nom du Père', 'Nom de la Mère'
    ])

    # Récupération et écriture des données
    actes = ActeNaissance.objects.all().order_by('-date_declaration')
    for acte in actes:
        date_dec = acte.date_declaration.strftime('%d/%m/%Y') if acte.date_declaration else ''
        
        # Récupération sécurisée du sexe pour le tableau Excel
        sexe_val = getattr(acte, 'sexe', 'M')
        sexe_display = "Féminin" if sexe_val == 'F' else "Masculin"

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

       # registre/views.py
       
       

# --- AJOUTEZ CECI À LA FIN DU FICHIER ---
def imprimer_certificat_residence(request, certificat_id):
    # On récupère les infos de l'étranger et de la sous-préfecture
    certificat = get_object_or_404(CertificatResidence, id=certificat_id)
    structure = Structure.objects.first()
    
    context = {
        'certificat': certificat,
        'structure': structure,
    }
    return render(request, 'registre/certificat_residence_print.html', context)