import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time

# ==============================================================================
#                 PARAMÈTRES (Homepage)
# ==============================================================================

TARGET_URL = "https://www.travisscott.com/"
# On surveille tout le corps de la page
BODY_SELECTOR = "body"
# On va lister tous les liens (a) et boutons (button)
LINKS_SELECTOR = "a, button"
HISTORY_FILE = "last_homepage_content.txt" # Fichier mémoire DÉDIÉ
CHANGES_FLAG_FILE = "homepage_changes.flag" # Fichier drapeau DÉDIÉ

# Récupération sécurisée des secrets
try:
    SENDER_EMAIL = "paulodi337@gmail.com"
    RECEIVER_EMAIL = "paulodi337@gmail.com"
    GMAIL_APP_PASSWORD = os.environ['GMAIL_APP_PASSWORD']
except KeyError:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERREUR: GMAIL_APP_PASSWORD non trouvé.")
    exit(1)

# ==============================================================================
#                 FONCTIONS DU BOT (Ne pas modifier)
# ==============================================================================

def send_notification(new_content_list):
    """Envoie une notification par email."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> Envoi de la notification par email...")
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"!!! ALERTE CHANGEMENT sur www.travisscott.com !!!"
    
    old_content_list = load_previous_content()
    
    body = f"""
    Bonjour,

    Le bot de surveillance a détecté un CHANGEMENT MAJEUR sur la page d'accueil : {TARGET_URL}
    (Une nouvelle banderole, un lien, ou une annonce de chaussures !)

    ANCIENNE LISTE DE LIENS/BOUTONS:
    {old_content_list}

    ---
    NOUVELLE LISTE DE LIENS/BOUTONS:
    {new_content_list}

    Vérifiez le site immédiatement !
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.close()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> Notification envoyée avec succès.")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] !!! Erreur lors de l'envoi de l'email : {e}")

def load_previous_content():
    """Charge le contenu stocké précédemment."""
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "N/A (Première exécution)"

def save_new_content(content):
    """Stocke le nouveau contenu pour la prochaine comparaison."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> Sauvegarde du nouveau contenu dans {HISTORY_FILE}...")
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    with open(CHANGES_FLAG_FILE, "w") as f:
        f.write("1")

def check_for_changes():
    """Fonction principale pour vérifier la page."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Vérification de {TARGET_URL}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'} 
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status() 
    except requests.RequestException as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] !!! Erreur de connexion : {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    page_body = soup.select_one(BODY_SELECTOR)
    if not page_body:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] !!! FATAL : Sélecteur 'body' non trouvé.")
        return

    all_links = page_body.select(LINKS_SELECTOR)
    
    current_links_list = []
    for link_tag in all_links:
        text = link_tag.get_text(strip=True)
        url = link_tag.get('href', 'pas de lien') # 'pas de lien' pour les boutons
        current_links_list.append(f"{text} ({url})")
    
    current_links_list.sort() # On trie pour éviter les fausses alertes
    
    current_content = "\n".join(current_links_list)
    previous_content = load_previous_content()

    if current_content != previous_content:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> Changement détecté. Enregistrement de la nouvelle base.")
        send_notification(current_content)
        save_new_content(current_content)
    else:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> Aucun changement détecté. (Page d'accueil identique)")

if __name__ == "__main__":
    check_for_changes()
