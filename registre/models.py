from django.db import models
from num2words import num2words

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

class ActeNaissance(models.Model):
    structure = models.ForeignKey(Structure, on_delete=models.CASCADE)
    numero_registre = models.IntegerField(default=1, verbose_name="N° Acte")
    annee_registre = models.IntegerField(default=2026, verbose_name="Année")
    date_declaration = models.DateField(verbose_name="Date de déclaration")

    # Identité de l'Enfant
    prenoms_enfant = models.CharField(max_length=255, verbose_name="Prénoms")
    nom_enfant = models.CharField(max_length=255, verbose_name="Nom")
    date_naissance = models.DateField(verbose_name="Né(e) le")
    heure_naissance = models.TimeField(verbose_name="À (Heure)", null=True, blank=True)
    lieu_naissance = models.CharField(max_length=255, verbose_name="Lieu de naissance")
# Ajoutez ces choix juste au début de votre modèle ActeNaissance
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    # Ajoutez ce champ avec les autres (nom, prénoms, etc.)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, default='M', verbose_name="Sexe de l'enfant")

    # Filiation (Parents)
    nom_pere = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom du Père")
    nationalite_pere = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nationalité Père")
    nom_mere = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom de la Mère")
    nationalite_mere = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nationalité Mère")

    # Mentions de Justice et Transcription
    transcription_justice = models.TextField(blank=True, null=True, verbose_name="Transcription / Jugement Supplétif")

    # Mentions Marginales (Mariage & Décès)
    date_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Marié(e) le")
    conjoint_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Avec")
    dissolution_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mariage dissous le")
    date_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Décédé(e) le")
    lieu_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lieu de décès")

    @property
    def numero_acte_complet(self):
        """Format : '01 du 02/12/2014'"""
        date_str = self.date_declaration.strftime('%d/%m/%Y')
        return f"{self.numero_registre:02d} du {date_str}"

    def infos_naissance_lettres(self):
        """Conversion conforme : 'mil' et 'premier' [cite: 2026-02-28]"""
        jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
                 "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", 
                 "dix-neuf", "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", 
                 "vingt-cinq", "vingt-six", "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
        
        d = self.date_naissance
        annee_lettres = num2words(d.year, lang='fr').replace('mille', 'mil')
        return f"{jours[d.day-1]} {d.strftime('%B')} {annee_lettres}"