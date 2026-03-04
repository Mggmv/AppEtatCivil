from django.db import models
from num2words import num2words

class Structure(models.Model):
    # Ajout de la préfecture pour la centralisation des données
    prefecture = models.CharField(max_length=255, verbose_name="Préfecture") 
    sous_prefecture = models.CharField(max_length=255, verbose_name="Sous-Préfecture")
    nom_centre = models.CharField(max_length=255, verbose_name="Nom du Centre")

    class Meta:
        verbose_name = "Structure Administrative"
        verbose_name_plural = "Structures Administratives"

    def __str__(self):
        # Affichage hiérarchique dans l'administration Django
        return f"{self.prefecture} > {self.sous_prefecture} > {self.nom_centre}"

class ActeNaissance(models.Model):
    structure = models.ForeignKey(Structure, on_delete=models.CASCADE)
    
    # Numérotation et Enregistrement
    numero_registre = models.IntegerField(default=1) 
    annee_registre = models.IntegerField(default=2026)
    date_declaration = models.DateField()

    # Identité de l'Enfant
    prenoms_enfant = models.CharField(max_length=255)
    nom_enfant = models.CharField(max_length=255)
    date_naissance = models.DateField()
    heure_naissance = models.TimeField()
    lieu_naissance = models.CharField(max_length=255)

    # Filiation
    nom_pere = models.CharField(max_length=255, blank=True, null=True)
    nationalite_pere = models.CharField(max_length=100, blank=True, null=True)
    nom_mere = models.CharField(max_length=255, blank=True, null=True)
    nationalite_mere = models.CharField(max_length=100, blank=True, null=True)

    # Transcription (Jugements supplétifs, etc.)
    transcription_justice = models.TextField(blank=True, null=True, verbose_name="Transcription")

    # MENTIONS MARGINALES (Maintenues selon vos instructions)
    date_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Marié le")
    conjoint_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Avec")
    dissolution_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mariage dissous (Date et décision)")
    date_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Décédé le")
    lieu_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lieu de décès")

    @property
    def numero_acte_complet(self):
        """Retourne le format N° XX/AAAA utilisé dans le QR Code et l'en-tête"""
        return f"{self.numero_registre:02d}/{self.annee_registre}"

    def nom_complet_officiel(self):
        return f"{self.prenoms_enfant.strip().title()} {self.nom_enfant.strip().upper()}"

    def infos_naissance_lettres(self):
        """
        Formatage conforme à l'administration ivoirienne :
        - 'mille' devient 'mil' [cite: 2026-02-28]
        - Le 1er du mois devient 'premier' [cite: 2026-02-28]
        """
        jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
                 "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", 
                 "dix-neuf", "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", 
                 "vingt-cinq", "vingt-six", "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
        
        mois_liste = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        
        d = self.date_naissance
        # Remplacement systématique de mille par mil pour la CI [cite: 2026-02-28]
        annee_lettres = num2words(d.year, lang='fr').replace('mille', 'mil')
        date_str = f"{jours[d.day-1]} {mois_liste[d.month-1]} {annee_lettres}"
        
        h = self.heure_naissance
        h_lettres = num2words(h.hour, lang='fr')
        m_lettres = num2words(h.minute, lang='fr')
        lbl_h = "heure" if h.hour <= 1 else "heures"
        min_str = "" if h.minute == 0 else f" {m_lettres} minutes"
        
        return {"date": date_str, "heure": f"{h_lettres} {lbl_h}{min_str}"}

    def __str__(self):
        return f"Acte {self.numero_acte_complet} - {self.nom_complet_officiel()}"
