import os
from pathlib import Path

# Chemin de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CONFIGURATION DE SÉCURITÉ ---
SECRET_KEY = 'votre-cle-secrete-ici' # Gardez celle que vous avez déjà
DEBUG = True # À mettre sur False en production réelle
ALLOWED_HOSTS = ['*'] # Permet le fonctionnement sur Render

# --- APPLICATIONS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'registre', # Votre application d'état civil
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Pour les fichiers statiques sur Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mon_projet.urls'

# --- GESTION DES TEMPLATES ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # ---> AJOUTEZ CETTE LIGNE ICI <---
                'registre.context_processors.infos_structure', 
            ],
        },
    },
]

WSGI_APPLICATION = 'mon_projet.wsgi.application'

# --- BASE DE DONNÉES ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- INTERNATIONALISATION (CI) 🇨🇮 ---
LANGUAGE_CODE = 'fr-fr'
# Fuseau horaire réglé sur Abidjan pour la validité des actes
TIME_ZONE = 'Africa/Abidjan' 
USE_I18N = True
USE_TZ = True

# --- FICHIERS STATIQUES ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'registre/static')]

# --- CONFIGURATION DES ACCÈS ---
# Redirige l'agent vers le Dashboard après connexion au lieu de /accounts/profile/
LOGIN_REDIRECT_URL = 'dashboard'
# Redirige vers la page d'accueil après déconnexion
LOGOUT_REDIRECT_URL = 'home'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'