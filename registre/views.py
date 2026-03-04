from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ActeNaissance # Nom exact corrigé ici

@login_required
def dashboard(request):
    # On récupère les 10 derniers actes de naissance
    derniers_actes = ActeNaissance.objects.all().order_by('-id')[:10]
    return render(request, 'registre/dashboard.html', {'actes': derniers_actes})

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

@login_required
def voir_extrait(request, pk):
    # On récupère les données de l'acte de naissance
    acte = get_object_or_404(ActeNaissance, pk=pk)
    return render(request, 'registre/extrait_naissance.html', {'acte': acte})
