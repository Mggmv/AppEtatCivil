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
    numero_registre = models.IntegerField(default=1) 
    annee_registre = models.IntegerField(default=2026)
    date_declaration = models.DateField()

    prenoms_enfant = models.CharField(max_length=255)
    nom_enfant = models.CharField(max_length=255)
    date_naissance = models.DateField()
    heure_naissance = models.TimeField()
    lieu_naissance = models.CharField(max_length=255)

    nom_pere = models.CharField(max_length=255, blank=True, null=True)
    nationalite_pere = models.CharField(max_length=100, blank=True, null=True)
    nom_mere = models.CharField(max_length=255, blank=True, null=True)
    nationalite_mere = models.CharField(max_length=100, blank=True, null=True)

    # Mentions Marginales
    date_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Marié le")
    conjoint_mariage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Avec")
    date_deces = models.CharField(max_length=255, blank=True, null=True, verbose_name="Décédé le")

    @property
    def numero_acte_complet(self):
        """Format exact demandé : '01 du 02/12/2014'"""
        date_str = self.date_declaration.strftime('%d/%m/%Y')
        [span_0](start_span)return f"{self.numero_registre:02d} du {date_str}"[span_0](end_span)

    def infos_naissance_lettres(self):
        # Respect des conventions ivoiriennes : "mil" et "premier" [cite: 2026-02-28]
        jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
                 "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", 
                 "dix-neuf", "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", 
                 "vingt-cinq", "vingt-six", "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
        d = self.date_naissance
        annee_lettres = num2words(d.year, lang='fr').replace('mille', 'mil')
        return f"{jours[d.day-1]} {d.strftime('%B')} {annee_lettres}"
