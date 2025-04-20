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
        """Attend que le chargement atteigne 100%"""
        print("Vérification approfondie...")
        test_cmd = self.phone.run_adb_command("pm list packages")
        if not self.phone.check_connection():
            print("Échec: Téléphone non connecté")
            return 0
        if "package:" not in test_cmd:
            print("ERREUR: Permission refusée - Activez le débogage USB")
            return 0

        attempt = 0
        last_percentage = 0
        
        while attempt < self.max_attempts:
            try:
                print("Capture de l'écran...")
                screenshot = self.phone.capture_screen()
                if screenshot is None:
                    print("Échec: Impossible de capturer l'écran")
                    raise ValueError("Capture d'écran échouée")
                
                # Détection du pourcentage
                percentage = self.detect_loading_percentage(screenshot)
                
                if percentage is not None:
                    print(f"Chargement: {percentage}%")
                    
                    if percentage == 100:
                        print("Chargement terminé!")
                        return 1
                    
                    # Vérification que la progression avance
                    if percentage > last_percentage:
                        last_percentage = percentage
                    else:
                        attempt += 1  # Stagnation
                else:
                    attempt += 1  # Échec détection
                    
            except Exception as e:
                print(f"Erreur: {str(e)}")
                attempt += 1
                
            time.sleep(self.check_interval)
        
        print("Timeout - Le chargement n'a pas atteint 100%")
        return 0

if __name__ == "__main__":
    loader = GameLoader()
    game_loaded = loader.wait_for_loading()
    
    if game_loaded == 1:
        print("Le jeu est prêt! game_loaded = 1")
    else:
        print("Échec du chargement")