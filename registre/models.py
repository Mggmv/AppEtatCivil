from django.db import models
from num2words import num2words

class Structure(models.Model):
    # Le default="Non précisée" est indispensable pour le déploiement
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
    numero_registre = models.IntegerField(default=1) 
    annee_registre = models.IntegerField(default=2026)
    date_declaration = models.DateField()

    # Identité
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

    # [span_3](start_span)Mentions Marginales[span_3](end_span)
    date_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Marié le")
    conjoint_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Avec")
    dissolution_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mariage dissous")
    date_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Décédé le")
    lieu_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lieu de décès")

    @property
    def numero_acte_complet(self):
        [span_4](start_span)"""Format demandé : '01 du 02/12/2014'[span_4](end_span)"""
        date_str = self.date_declaration.strftime('%d/%m/%Y')
        return f"{self.numero_registre:02d} du {date_str}"

    def nom_complet_officiel(self):
        return f"{self.prenoms_enfant.strip().title()} {self.nom_enfant.strip().upper()}"

    def infos_naissance_lettres(self):
        [span_5](start_span)[span_6](start_span)"""Conformité CI : 'mil' et 'premier'[span_5](end_span)[span_6](end_span)"""
        jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
                 "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", 
                 "dix-neuf", "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", 
                 "vingt-cinq", "vingt-six", "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
        
        d = self.date_naissance
        [span_7](start_span)annee_lettres = num2words(d.year, lang='fr').replace('mille', 'mil')[span_7](end_span)
        date_str = f"{jours[d.day-1]} {d.strftime('%B')} {annee_lettres}"
        return date_str
