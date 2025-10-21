import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time

# ==============================================================================
#                 PARAMÈTRES (lus depuis GitHub)
# ==============================================================================

TARGET_URL = "https://music.travisscott.com"
# LE NOUVEAU SÉLECTEUR CORRECT :
SELECTOR = '[id^="shopify-section-section_collection_"]' 
HISTORY_FILE = "last_content.txt" # Fichier de sauvegarde

# Récupération sécurisée des secrets
try:
    SENDER_EMAIL = "paulodi337@gmail.com"
    RECEIVER_EMAIL = "paulodi337@gmail.com"
    GMAIL_APP_PASSWORD = os.environ['GMAIL_APP_PASSWORD']
except KeyError:
    print("ERREUR: GMAIL_APP_PASSWORD non trouvé dans les secrets GitHub.")
    exit(1)

# ==============================================================================
#                 FONCTIONS DU BOT (Ne pas modifier)
# ==============================================================================

def send_notification(new_content):
    """Envoie une notification par email."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> Envoi de la notification par email...")
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"[ALERTE BOT] NOUVEAU PRODUIT DÉTECTÉ sur {TARGET_URL}"
    
    old_content = load_previous_content()
    body = f"""
    Bonjour,

    Le bot de surveillance a détecté un NOUVEAU CONTENU sur la page : {TARGET_URL}
    Cela signifie probablement qu'un nouveau produit a été ajouté !

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
    # Crée un fichier "flag" pour dire au planificateur de sauvegarder
    with open("changes_detected.flag", "w") as f:
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
    target_element = soup.select_one(SELECTOR)

    # Version propre du bloc d'erreur (sans l'enquête)
    if not target_element:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] !!! FATAL : Sélecteur '{SELECTOR}' non trouvé. Le site a peut-être changé.")
        return

    current_content = target_element.prettify()
    previous_content = load_previous_content()

    if current_content != previous_content:
        # C'est ce qui va se passer maintenant, car "init" est différent du vrai site
        if previous_content == "N/A (Première exécution)" or previous_content == "init": 
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> Première exécution. Contenu initial enregistré.")
            send_notification(current_content) # Envoie un email à la première exécution !
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> CHANGEMENT DÉTECTÉ ! Envoi de l'alerte.")
            send_notification(current_content)
        save_new_content(current_content)
    else:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> Aucun changement détecté.")

if __name__ == "__main__":
    check_for_changes()
