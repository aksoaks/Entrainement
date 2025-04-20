from game_loader import GameLoader
from phone_controller import PhoneController
import logging
import subprocess

subprocess.call([r"D:\Users\Documents\Code\Python\Entrainement\update_git.bat"])

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():

    phone = PhoneController()
    print("Test ADB:")
    print("Résolution:", phone.resolution)
    print("Capture d'écran...")
    img = phone.capture_screen()
    print("Taille image:", img.shape if img is not None else "Échec")

    logging.info("Initialisation du système...")
    loader = GameLoader()
    
    if loader.wait_for_loading() == 1:
        logging.info("Jeu complètement chargé!")
    else:
        logging.error("Échec du chargement")


if __name__ == "__main__":
    try:
        loader = GameLoader()
        if loader.wait_for_loading() == 1:
            print("Jeu prêt!")
        else:
            print("Échec du chargement")

    except Exception as e:
        print(f"Erreur : {e}")