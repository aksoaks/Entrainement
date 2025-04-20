import cv2
import pytesseract
import numpy as np
import re
import time
from phone_controller import PhoneController  # Modification ici
from utils.image_utils import detect_loading_percentage  # Déplacé dans utils

class GameLoader:
    def __init__(self):
        self.phone = PhoneController()
        self.loading_roi = (1000, 940, 250, 40)  # x, y, width, height
        self.max_attempts = 30  # Nombre max de tentatives avant timeout
        self.check_interval = 2  # Intervalle entre les vérifications en secondes

    def detect_loading_percentage(self, image):
        """Détecte le pourcentage de chargement depuis une image"""
        try:
            # Extraction de la ROI
            x, y, w, h = self.loading_roi
            roi = image[y:y+h, x:x+w]
            
            # Prétraitement pour OCR
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            mask = cv2.inRange(blurred, 180, 255)
            kernel = np.ones((2, 2), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=1)
            
            # Reconnaissance du texte
            custom_config = r'--psm 7 --oem 3 -l fra+eng'
            text = pytesseract.image_to_string(mask, config=custom_config).strip()
            
            # Extraction du pourcentage
            match = re.search(r'(\d{1,3})\s*%', text)
            return int(match.group(1)) if match else None
            
        except Exception as e:
            print(f"Erreur détection: {str(e)}")
            return None

    def wait_for_loading(self):
        """Version corrigée avec gestion améliorée"""
        print("Vérification approfondie de la connexion...")
        
        # Test matériel supplémentaire
        device_model = self.phone.run_adb_command("getprop ro.product.model")
        print(f"Modèle détecté: {device_model}")
        
        if not self.phone.check_connection():
            print("ERREUR: Vérifiez:")
            print("- Débogage USB activé")
            print("- Autorisation accordée")
            print("- Câble USB fonctionnel")
            return 0

        print("Début du monitoring de chargement...")
        attempt = 0
        last_percentage = 0
        
        while attempt < self.max_attempts:
            try:
                print(f"Tentative {attempt + 1}/{self.max_attempts}")
                screenshot = self.phone.capture_screen("current_screen.png")
                
                if screenshot is None:
                    raise ValueError("Échec capture écran")
                
                percentage = self.detect_loading_percentage(screenshot)
                
                if percentage is None:
                    print("Aucun pourcentage détecté - vérifiez la ROI")
                    attempt += 1
                    continue
                    
                print(f"Progression: {percentage}%")
                
                if percentage == 100:
                    print("✅ Chargement complet!")
                    return 1
                    
                if percentage <= last_percentage:
                    print("⚠️ Progression stagnante")
                    attempt += 1
                else:
                    last_percentage = percentage
                    
            except Exception as e:
                print(f"ERREUR: {str(e)}")
                attempt += 1
                
            time.sleep(self.check_interval)
        
        print("❌ Timeout atteint")
        return 0

if __name__ == "__main__":
    loader = GameLoader()
    game_loaded = loader.wait_for_loading()
    
    if game_loaded == 1:
        print("Le jeu est prêt! game_loaded = 1")
    else:
        print("Échec du chargement")