import os
import sys
import threading
import time
import shutil
from datetime import datetime

# --- 1. SÉCURITÉ DES CHEMINS (Spécial Mode Silencieux) ---
# On force le logiciel à regarder dans son propre dossier pour trouver mon_projet
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- 2. SÉCURITÉ ANTI-PLANTAGE SANS CONSOLE ---
# En mode silencieux, la console n'existe plus. 
# On redirige les messages d'erreur vers le "vide" pour que Django ne plante pas.
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mon_projet.settings')

def backup_database():
    source = os.path.join(BASE_DIR, 'db.sqlite3')
    sauvegardes_dir = os.path.join(BASE_DIR, 'sauvegardes')
    
    if os.path.exists(source):
        if not os.path.exists(sauvegardes_dir):
            os.makedirs(sauvegardes_dir)
        timestamp = datetime.now().strftime('%Y-%m-%d_%Hh%M')
        destination = os.path.join(sauvegardes_dir, f'backup_{timestamp}.sqlite3')
        try:
            shutil.copy2(source, destination)
        except Exception:
            pass

def start_django():
    from django.core.management import execute_from_command_line
    try:
        execute_from_command_line([sys.argv[0], 'runserver', '127.0.0.1:8026', '--noreload'])
    except Exception as e:
        # En cas d'erreur grave, on crée un fichier texte invisible au lieu de crasher
        import traceback
        with open(os.path.join(BASE_DIR, "erreur_serveur.txt"), "w") as f:
            f.write("Erreur au démarrage :\n")
            f.write(traceback.format_exc())

def open_browser():
    time.sleep(3)
    try:
        os.startfile('http://127.0.0.1:8026/admin/')
    except Exception:
        pass

if __name__ == "__main__":
    backup_database()
    threading.Thread(target=open_browser, daemon=True).start()
    start_django()