from django.db import models
from num2words import num2words
import re # Ajouté pour lire automatiquement les années dans le texte libre

class Structure(models.Model):
    region = models.CharField(max_length=100, verbose_name="Région", null=True, blank=True, help_text="Ex: DU CAVALLY")
    prefecture = models.CharField(max_length=100, verbose_name="Département / Préfecture")
    sous_prefecture = models.CharField(max_length=100, verbose_name="Sous-Préfecture")
    nom_centre = models.CharField(max_length=100, verbose_name="Nom du centre")

    class Meta:
        verbose_name = "Structure Administrative"
        verbose_name_plural = "Structures Administratives"

    def __str__(self):
        return f"{self.prefecture} > {self.sous_prefecture} > {self.nom_centre}"

class CertificatResidence(models.Model):
    numero_certificat = models.CharField(max_length=50, verbose_name="Numéro de Registre", unique=True)
    date_etablissement = models.DateField(verbose_name="Date d'établissement")
    
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenoms = models.CharField(max_length=150, verbose_name="Prénoms")
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')], default='M', verbose_name="Sexe")
    date_naissance = models.DateField(verbose_name="Date de naissance")
    lieu_naissance = models.CharField(max_length=100, verbose_name="Lieu de naissance")
    nationalite = models.CharField(max_length=100, verbose_name="Nationalité")
    profession = models.CharField(max_length=100, verbose_name="Profession", blank=True, null=True)
    
    piece_identite = models.CharField(max_length=100, verbose_name="Pièce d'identité (Type et N°)", help_text="Ex: CNI (CC) : BF. 38400...")
    adresse_locale = models.CharField(max_length=200, verbose_name="Adresse / Quartier")

    # --- NOUVEAUX CHAMPS AJOUTÉS ---
    nom_pere = models.CharField(max_length=150, verbose_name="Fils/Fille de (Nom du père)", null=True, blank=True)
    nom_mere = models.CharField(max_length=150, verbose_name="et de (Nom de la mère)", null=True, blank=True)
    resident_depuis = models.CharField(max_length=4, verbose_name="Résident depuis (Année)", help_text="Ex: 2020", null=True, blank=True)

    class Meta:
        verbose_name = "Certificat de Résidence"
        verbose_name_plural = "Certificats de Résidence"

    def __str__(self):
        return f"Certificat N°{self.numero_certificat} - {self.nom} {self.prenoms}"

# ==========================================
# ACTE DE NAISSANCE
# ==========================================
class ActeNaissance(models.Model):
    # 1. L'ENFANT ET LE REGISTRE
    structure = models.ForeignKey('Structure', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Structure d'état civil")
    numero_registre = models.CharField(max_length=50, verbose_name="N° de l'acte")
    annee_registre = models.CharField(max_length=4, verbose_name="Année du registre")
    date_declaration = models.DateField(verbose_name="Date de declaration", null=True, blank=True)

    nom_enfant = models.CharField(max_length=150, verbose_name="Nom de l'enfant")
    
    # MODIFICATION : Prénoms facultatifs
    prenoms_enfant = models.CharField(max_length=200, verbose_name="Prénoms de l'enfant", blank=True, null=True)
    
    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], verbose_name="Sexe")
    
    # MODIFICATION : Date de naissance en champ texte libre
    date_naissance = models.CharField(max_length=150, verbose_name="Date de naissance (ou Année)", blank=True, null=True, help_text="Ex: 12/05/2004 ou 2004")
    
    heure_naissance = models.TimeField(verbose_name="Heure de naissance", null=True, blank=True)
    lieu_naissance = models.CharField(max_length=200, verbose_name="Lieu de naissance")

    # 2. FILIATION (PÈRE ET MÈRE)
    nom_pere = models.CharField(max_length=200, verbose_name="Nom et prénoms du père", blank=True, null=True)
    date_naissance_pere = models.CharField(max_length=150, verbose_name="Né le/vers (Père)", blank=True, null=True)
    profession_pere = models.CharField(max_length=150, verbose_name="Profession du père", blank=True, null=True)
    domicile_pere = models.CharField(max_length=200, verbose_name="Domicilié à (Père)", blank=True, null=True)
    nationalite_pere = models.CharField(max_length=100, verbose_name="Nationalité du père", default="Ivoirienne", blank=True, null=True)

    nom_mere = models.CharField(max_length=200, verbose_name="Nom et prénoms de la mère", blank=True, null=True)
    date_naissance_mere = models.CharField(max_length=150, verbose_name="Née le/vers (Mère)", blank=True, null=True)
    profession_mere = models.CharField(max_length=150, verbose_name="Profession de la mère", blank=True, null=True)
    domicile_mere = models.CharField(max_length=200, verbose_name="Domiciliée à (Mère)", blank=True, null=True)
    nationalite_mere = models.CharField(max_length=100, verbose_name="Nationalité de la mère", default="Ivoirienne", blank=True, null=True)

    # 3. MENTIONS ÉVENTUELLES ET JUSTICE
    date_mariage = models.CharField(max_length=150, verbose_name="Date de mariage", blank=True, null=True)
    conjoint_mariage = models.CharField(max_length=200, verbose_name="Conjoint(e)", blank=True, null=True)
    dissolution_mariage = models.CharField(max_length=150, verbose_name="Date de dissolution du mariage", blank=True, null=True)
    date_deces = models.CharField(max_length=150, verbose_name="Date de décès", blank=True, null=True)
    lieu_deces = models.CharField(max_length=200, verbose_name="Lieu de décès", blank=True, null=True)
    
    transcription_justice = models.TextField(verbose_name="Transcription de décision de justice", blank=True, null=True)
    nom_sous_prefet = models.CharField(max_length=150, verbose_name="Nom et Prénoms du Sous-préfet", blank=True, null=True, help_text="Ex: TRA Bi Bah Albert")
    nom_officier_creation = models.CharField(max_length=150, blank=True, null=True, verbose_name="Officier d'état civil (Créateur de l'acte)")


    class Meta:
        verbose_name = "Acte de Naissance"
        verbose_name_plural = "Actes de Naissance"

    def __str__(self):
        pr = self.prenoms_enfant if self.prenoms_enfant else ""
        return f"Acte N°{self.numero_registre} - {self.nom_enfant} {pr}"

    # ==========================================
    # FONCTIONS DE CONVERSION EN LETTRES
    # ==========================================
    
    @property
    def infos_naissance_lettres(self):
        if not self.date_naissance:
            return ""
            
        valeur = str(self.date_naissance).strip()
        from num2words import num2words
        jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
                 "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", 
                 "dix-neuf", "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", 
                 "vingt-cinq", "vingt-six", "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
        mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        
        try:
            if '-' in valeur and len(valeur.split('-')) == 3:
                parts = valeur.split('-')
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                annee_lettres = num2words(y, lang='fr').replace('mille', 'mil')
                return f"{jours[d-1]} {mois[m-1]} {annee_lettres}"

            elif '/' in valeur and len(valeur.split('/')) == 3:
                parts = valeur.split('/')
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                annee_lettres = num2words(y, lang='fr').replace('mille', 'mil')
                return f"{jours[d-1]} {mois[m-1]} {annee_lettres}"

            match = re.search(r'\b(19|20)\d{2}\b', valeur)
            if match:
                y = int(match.group())
                annee_lettres = num2words(y, lang='fr').replace('mille', 'mil')
                return annee_lettres

        except Exception:
            pass

        return valeur 

    @property
    def date_declaration_lettres(self):
        if not self.date_declaration:
            return ""
        if isinstance(self.date_declaration, str):
            return self.date_declaration

        from num2words import num2words
        jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
                 "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", 
                 "dix-neuf", "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", 
                 "vingt-cinq", "vingt-six", "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
        mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        
        d = self.date_declaration
        annee_lettres = num2words(d.year, lang='fr').replace('mille', 'mil')
        return f"{jours[d.day-1]} {mois[d.month-1]} {annee_lettres}"

    @property
    def heure_naissance_lettres(self):
        if not self.heure_naissance:
            return ""
        if isinstance(self.heure_naissance, str):
            return self.heure_naissance
        
        from num2words import num2words
        h = self.heure_naissance.hour
        m = self.heure_naissance.minute
        
        if h == 0 and m == 0:
            return "minuit"
        elif h == 12 and m == 0:
            return "midi"
        
        heure_str = "minuit" if h == 0 else "midi" if h == 12 else f"{num2words(h, lang='fr')} heure{'s' if h > 1 else ''}"
        minute_str = "" if m == 0 else f" {num2words(m, lang='fr')} minute{'s' if m > 1 else ''}"
        return f"{heure_str}{minute_str}"

class CertificatCelibat(models.Model):
    numero_certificat = models.CharField(max_length=50, verbose_name="Numéro du Certificat", help_text="Ex: 012 RC/D.TLP/ SP-TLP")
    date_etablissement = models.DateField(verbose_name="Date d'établissement")
    nom_officier = models.CharField(max_length=150, verbose_name="Nom de l'Officier (Sous-préfet)")
    annee_registre_naissance = models.CharField(max_length=4, verbose_name="Année du Registre de Naissance", help_text="Ex: 1974")
    numero_acte_naissance = models.CharField(max_length=50, verbose_name="N° de l'acte de naissance")
    date_acte_naissance = models.DateField(verbose_name="Date de l'acte de naissance")
    nom_prenoms = models.CharField(max_length=200, verbose_name="Nom et Prénoms")
    date_naissance = models.DateField(verbose_name="Date de naissance")
    lieu_naissance = models.CharField(max_length=100, verbose_name="Lieu de naissance")
    nom_pere = models.CharField(max_length=150, verbose_name="Fils / Fille de (Père)")
    nom_mere = models.CharField(max_length=150, verbose_name="Et de (Mère)")
    nationalite = models.CharField(max_length=100, verbose_name="Nationalité", default="Ivoirienne")
    domicile = models.CharField(max_length=150, verbose_name="Domicile")
    profession = models.CharField(max_length=100, verbose_name="Profession")

    class Meta:
        verbose_name = "Certificat de Célibat"
        verbose_name_plural = "Certificats de Célibat"

    def __str__(self):
        return f"Certificat N°{self.numero_certificat} - {self.nom_prenoms}"

class CertificatNonDeces(models.Model):
    numero_certificat = models.CharField(max_length=50, verbose_name="Numéro du Certificat", help_text="Ex: 2023/______/SP-TLP")
    date_etablissement = models.DateField(verbose_name="Date d'établissement")
    nom_officier = models.CharField(max_length=150, verbose_name="Nom de l'Officier (Sous-préfet)")
    annee_registre = models.CharField(max_length=4, verbose_name="Année du registre vérifié")
    nom_defunt = models.CharField(max_length=200, verbose_name="Nom et Prénoms du défunt")
    date_lieu_naissance_defunt = models.CharField(max_length=200, verbose_name="Né(e) le/vers et à", help_text="Ex: vers 1930 à Ziombli")
    nom_pere = models.CharField(max_length=150, verbose_name="Fils / Fille de (Père)")
    nom_mere = models.CharField(max_length=150, verbose_name="Et de (Mère)")
    date_deces = models.CharField(max_length=100, verbose_name="Date présumée du décès", help_text="Ex: 1er janvier 1975 ou 2009")
    lieu_deces = models.CharField(max_length=150, verbose_name="Lieu du décès", help_text="Ex: Ziombli, Sous-Préfecture de Toulépleu")
    nom_declarant = models.CharField(max_length=150, verbose_name="Nom du déclarant")
    infos_declarant = models.CharField(max_length=255, verbose_name="Infos (Naissance, profession, domicile)", help_text="Ex: né(e) le 29/12/1953 à Méo, Planteur à Méo")
    nom_temoin1 = models.CharField(max_length=150, verbose_name="Nom du 1er témoin")
    infos_temoin1 = models.CharField(max_length=255, verbose_name="Infos 1er témoin", help_text="Ex: né le 01/01/1954 à Ziombli, planteur à Ziombli")
    cni_temoin1 = models.CharField(max_length=200, verbose_name="Pièce d'identité 1er témoin", blank=True, null=True, help_text="Ex: CNI N° C 0099 2173 07 du 23/10/2009 à Toulepleu")
    nom_temoin2 = models.CharField(max_length=150, verbose_name="Nom du 2ème témoin", blank=True, null=True)
    infos_temoin2 = models.CharField(max_length=255, verbose_name="Infos 2ème témoin", blank=True, null=True)
    cni_temoin2 = models.CharField(max_length=200, verbose_name="Pièce d'identité 2ème témoin", blank=True, null=True)

    class Meta:
        verbose_name = "Certificat de Non Déclaration de Décès"
        verbose_name_plural = "Certificats de Non Déclaration de Décès"

    def __str__(self):
        return f"N°{self.numero_certificat} - Défunt: {self.nom_defunt}"

class CertificatNonDivorce(models.Model):
    numero_certificat = models.CharField(max_length=50, verbose_name="Numéro du Certificat", blank=True, null=True)
    date_etablissement = models.DateField(verbose_name="Date d'établissement")
    nom_officier = models.CharField(max_length=150, verbose_name="Nom de l'Officier (Sous-préfet)")
    annee_registre_naissance = models.CharField(max_length=4, verbose_name="Année du Registre de Naissance")
    numero_acte_naissance = models.CharField(max_length=50, verbose_name="N° de l'acte de naissance")
    date_acte_naissance = models.DateField(verbose_name="Date de l'acte de naissance")
    nom_prenoms = models.CharField(max_length=200, verbose_name="Nom et Prénoms")
    date_naissance = models.DateField(verbose_name="Date de naissance")
    lieu_naissance = models.CharField(max_length=100, verbose_name="Lieu de naissance")
    nom_pere = models.CharField(max_length=150, verbose_name="Fils / Fille de (Père)")
    nom_mere = models.CharField(max_length=150, verbose_name="Et de (Mère)")
    nationalite = models.CharField(max_length=100, verbose_name="Nationalité", default="Ivoirienne")
    domicile = models.CharField(max_length=150, verbose_name="Domicile")
    profession = models.CharField(max_length=100, verbose_name="Profession")

    class Meta:
        verbose_name = "Certificat de Non Divorce"
        verbose_name_plural = "Certificats de Non Divorce"

    def __str__(self):
        return f"Non Divorce - {self.nom_prenoms}"

class CertificatNonRemariage(models.Model):
    numero_certificat = models.CharField(max_length=50, verbose_name="Numéro du Certificat", blank=True, null=True)
    date_etablissement = models.DateField(verbose_name="Date d'établissement")
    nom_officier = models.CharField(max_length=150, verbose_name="Nom de l'Officier (Sous-préfet)")
    annee_registre_naissance = models.CharField(max_length=4, verbose_name="Année du Registre de Naissance")
    numero_acte_naissance = models.CharField(max_length=50, verbose_name="N° de l'acte de naissance")
    date_acte_naissance = models.DateField(verbose_name="Date de l'acte de naissance")
    nom_prenoms = models.CharField(max_length=200, verbose_name="Nom et Prénoms")
    date_naissance = models.DateField(verbose_name="Date de naissance")
    lieu_naissance = models.CharField(max_length=100, verbose_name="Lieu de naissance")
    nom_pere = models.CharField(max_length=150, verbose_name="Fils / Fille de (Père)")
    nom_mere = models.CharField(max_length=150, verbose_name="Et de (Mère)")
    nationalite = models.CharField(max_length=100, verbose_name="Nationalité", default="Ivoirienne")
    domicile = models.CharField(max_length=150, verbose_name="Domicile")
    profession = models.CharField(max_length=100, verbose_name="Profession")

    class Meta:
        verbose_name = "Certificat de Non Remariage"
        verbose_name_plural = "Certificats de Non Remariage"

    def __str__(self):
        return f"Non Remariage - {self.nom_prenoms}"

class CertificatNonSeparationCorps(models.Model):
    numero_certificat = models.CharField(max_length=50, verbose_name="Numéro du Certificat", blank=True, null=True)
    date_etablissement = models.DateField(verbose_name="Date d'établissement")
    nom_officier = models.CharField(max_length=150, verbose_name="Nom de l'Officier (Sous-préfet)")
    annee_registre_naissance = models.CharField(max_length=4, verbose_name="Année du Registre")
    numero_acte_naissance = models.CharField(max_length=50, verbose_name="N° de l'acte de naissance")
    date_acte_naissance = models.CharField(max_length=100, verbose_name="Date de l'acte de naissance", help_text="Ex: 07/01/1985")
    nom_prenoms = models.CharField(max_length=200, verbose_name="Nom et Prénoms")
    date_naissance = models.CharField(max_length=100, verbose_name="Né(e) le / vers", help_text="Ex: 01/01/1985 ou Vers 1925")
    lieu_naissance = models.CharField(max_length=100, verbose_name="Lieu de naissance")
    nom_pere = models.CharField(max_length=150, verbose_name="Fils / Fille de (Père)")
    nom_mere = models.CharField(max_length=150, verbose_name="Et de (Mère)")
    nationalite = models.CharField(max_length=100, verbose_name="Nationalité", default="Ivoirienne")
    domicile = models.CharField(max_length=150, verbose_name="Domicile")
    profession = models.CharField(max_length=100, verbose_name="Profession")

    class Meta:
        verbose_name = "Certificat de Non Séparation de Corps"
        verbose_name_plural = "Certificats de Non Séparation de Corps"

    def __str__(self):
        return f"Non Séparation - {self.nom_prenoms}"

class CertificatVie(models.Model):
    numero_certificat = models.CharField(max_length=50, verbose_name="Numéro du Certificat", blank=True, null=True)
    date_etablissement = models.DateField(verbose_name="Date d'établissement")
    nom_officier = models.CharField(max_length=150, verbose_name="Nom de l'Officier (Sous-préfet)")
    annee_registre_naissance = models.CharField(max_length=4, verbose_name="Année du Registre")
    numero_acte_naissance = models.CharField(max_length=50, verbose_name="N° de l'acte de naissance")
    date_acte_naissance = models.CharField(max_length=100, verbose_name="Date de l'acte de naissance")
    nom_prenoms = models.CharField(max_length=200, verbose_name="Nom et Prénoms")
    date_naissance = models.CharField(max_length=100, verbose_name="Né(e) le / vers", help_text="Ex: 31/12/1950 ou Vers 1925")
    lieu_naissance = models.CharField(max_length=100, verbose_name="Lieu de naissance")
    nom_pere = models.CharField(max_length=150, verbose_name="Fils / Fille de (Père)")
    nom_mere = models.CharField(max_length=150, verbose_name="Et de (Mère)")
    nationalite = models.CharField(max_length=100, verbose_name="Nationalité", default="Ivoirienne")
    domicile = models.CharField(max_length=150, verbose_name="Domicile")
    profession = models.CharField(max_length=100, verbose_name="Profession")

    class Meta:
        verbose_name = "Certificat de Vie"
        verbose_name_plural = "Certificats de Vie"

    def __str__(self):
        return f"Certificat de Vie - {self.nom_prenoms}"

class ActeMariage(models.Model):
    numero_registre = models.CharField(max_length=50, verbose_name="N° de l'acte")
    annee_registre = models.CharField(max_length=4, verbose_name="Année du registre")
    date_mariage = models.DateField(verbose_name="Date du mariage")
    date_etablissement = models.DateField(verbose_name="Date d'établissement de l'extrait")
    nom_officier = models.CharField(max_length=150, verbose_name="Nom de l'Officier d'état civil")

    nom_prenoms_epoux = models.CharField(max_length=255, verbose_name="Nom et Prénoms de l'Époux")
    date_naissance_epoux = models.CharField(max_length=150, verbose_name="Né le / Vers", help_text="Ex: Vers 1920 ou 12/05/1980")
    lieu_naissance_epoux = models.CharField(max_length=150, verbose_name="À (Lieu de naissance)")
    nationalite_epoux = models.CharField(max_length=100, verbose_name="Nationalité de l'époux", default="Ivoirienne")
    pere_epoux = models.CharField(max_length=150, verbose_name="Fils de (Père)")
    nationalite_pere_epoux = models.CharField(max_length=100, verbose_name="Nationalité du père", blank=True, null=True)
    mere_epoux = models.CharField(max_length=150, verbose_name="Et de (Mère)")
    nationalite_mere_epoux = models.CharField(max_length=100, verbose_name="Nationalité de la mère", blank=True, null=True)
    domicile_parents_epoux = models.CharField(max_length=200, verbose_name="Domiciliés à (Parents)", blank=True, null=True)

    nom_prenoms_epouse = models.CharField(max_length=255, verbose_name="Nom et Prénoms de l'Épouse")
    date_naissance_epouse = models.CharField(max_length=150, verbose_name="Née le / Vers")
    lieu_naissance_epouse = models.CharField(max_length=150, verbose_name="À (Lieu de naissance)")
    nationalite_epouse = models.CharField(max_length=100, verbose_name="Nationalité de l'épouse", default="Ivoirienne")
    pere_epouse = models.CharField(max_length=150, verbose_name="Fille de (Père)")
    nationalite_pere_epouse = models.CharField(max_length=100, verbose_name="Nationalité du père", blank=True, null=True)
    mere_epouse = models.CharField(max_length=150, verbose_name="Et de (Mère)")
    nationalite_mere_epouse = models.CharField(max_length=100, verbose_name="Nationalité de la mère", blank=True, null=True)
    domicile_parents_epouse = models.CharField(max_length=200, verbose_name="Domiciliés à (Parents)", blank=True, null=True)

    mentions_marginales = models.TextField(blank=True, null=True, verbose_name="Mentions (Divorce, Décès, etc.)")

    class Meta:
        verbose_name = "Extrait de Mariage"
        verbose_name_plural = "Extraits de Mariage"

    def __str__(self):
        return f"Mariage N°{self.numero_registre} : {self.nom_prenoms_epoux} & {self.nom_prenoms_epouse}"

    @property
    def date_mariage_lettres(self):
        if not self.date_mariage:
            return ""
        from num2words import num2words
        jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
                 "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", 
                 "dix-neuf", "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", 
                 "vingt-cinq", "vingt-six", "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
        mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        
        d = self.date_mariage
        annee_lettres = num2words(d.year, lang='fr').replace('mille', 'mil')
        return f"{jours[d.day-1]} {mois[d.month-1]} {annee_lettres}"
