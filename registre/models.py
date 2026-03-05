from django.db import models
from num2words import num2words

class Structure(models.Model):
    prefecture = models.CharField(max_length=255, verbose_name="Préfecture", default="Non précisée") 
    sous_prefecture = models.CharField(max_length=255, verbose_name="Sous-Préfecture")
    nom_centre = models.CharField(max_length=255, verbose_name="Nom du Centre")

    class Meta:
        verbose_name = "Structure Administrative"
        verbose_name_plural = "Structures Administratives"

    def __str__(self):
        return f"{self.prefecture} > {self.sous_prefecture} > {self.nom_centre}"

class ActeNaissance(models.Model):
    structure = models.ForeignKey(Structure, on_delete=models.CASCADE)
    
    # Enregistrement
    numero_registre = models.IntegerField(default=1, verbose_name="N° Acte") 
    annee_registre = models.IntegerField(default=2026, verbose_name="Année")
    date_declaration = models.DateField(verbose_name="Date de déclaration")

    # Identité de l'Enfant
    prenoms_enfant = models.CharField(max_length=255, verbose_name="Prénoms")
    nom_enfant = models.CharField(max_length=255, verbose_name="Nom")
    date_naissance = models.DateField(verbose_name="Né(e) le")
    heure_naissance = models.TimeField(verbose_name="Heure de naissance")
    lieu_naissance = models.CharField(max_length=255, verbose_name="Lieu de naissance")

    # Filiation complète [Nouveau]
    nom_pere = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom du Père")
    nationalite_pere = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nationalité Père")
    nom_mere = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom de la Mère")
    nationalite_mere = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nationalité Mère")

    # Transcription et Jugement [Nouveau]
    transcription_justice = models.TextField(blank=True, null=True, verbose_name="Transcription / Jugement Supplétif")

    # Mentions Marginales complètes [Nouveau]
    date_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Marié(e) le")
    conjoint_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Avec")
    dissolution_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mariage dissous le")
    date_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Décédé(e) le")
    lieu_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lieu de décès")

    @property
    def numero_acte_complet(self):
        [span_1](start_span)[span_2](start_span)"""Format : '01 du 02/12/2014'[span_1](end_span)[span_2](end_span)"""
        date_str = self.date_declaration.strftime('%d/%m/%Y')
        return f"{self.numero_registre:02d} du {date_str}"

    def infos_naissance_lettres(self):
        [span_3](start_span)"""Conventions : 'mil' et 'premier'[span_3](end_span)"""
        jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
                 "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", 
                 "dix-neuf", "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", 
                 "vingt-cinq", "vingt-six", "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
        d = self.date_naissance
        annee_lettres = num2words(d.year, lang='fr').replace('mille', 'mil')
        return f"{jours[d.day-1]} {d.strftime('%B')} {annee_lettres}"
