from django.db import models
from num2words import num2words

class Structure(models.Model):
    nom_centre = models.CharField(max_length=255)
    sous_prefecture = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nom_centre} ({self.sous_prefecture})"

class ActeNaissance(models.Model):
    structure = models.ForeignKey(Structure, on_delete=models.CASCADE)
    
    # Numérotation
    numero_registre = models.IntegerField(default=1) 
    annee_registre = models.IntegerField(default=2026) # Champ requis par la migration
    date_declaration = models.DateField()

    # Enfant
    prenoms_enfant = models.CharField(max_length=255)
    nom_enfant = models.CharField(max_length=255)
    date_naissance = models.DateField()
    heure_naissance = models.TimeField()
    lieu_naissance = models.CharField(max_length=255)

    # Filiation (Autorise Inconnu et Nationalité vide)
    nom_pere = models.CharField(max_length=255, blank=True, null=True)
    nationalite_pere = models.CharField(max_length=100, blank=True, null=True)
    nom_mere = models.CharField(max_length=255, blank=True, null=True)
    nationalite_mere = models.CharField(max_length=100, blank=True, null=True)

    # Transcription et Mentions
    transcription_justice = models.TextField(blank=True, null=True)
     # Mentions marginales (Champs texte pour plus de flexibilité)
    date_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Marié le")
    conjoint_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Avec")
    # Ce champ inclut désormais la date et la décision
    dissolution_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mariage dissous (Date et décision)")
    date_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Décédé le")
    lieu_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lieu de décès")
    @property
    def numero_acte_complet(self):
        return f"{self.numero_registre:02d}/{self.annee_registre}"

    def nom_complet_officiel(self):
        """Corrige l'erreur AttributeError"""
        return f"{self.prenoms_enfant.strip().title()} {self.nom_enfant.strip().upper()}"

    def infos_naissance_lettres(self):
        """Format ivoirien : 'mil' et 'premier' [cite: 2026-02-28]"""
        jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
                 "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", 
                 "dix-neuf", "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", 
                 "vingt-cinq", "vingt-six", "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
        mois_liste = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        
        d = self.date_naissance
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