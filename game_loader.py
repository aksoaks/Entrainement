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

    def is_green_loaded(self, image):
        """Détecte si l'écran est dominé par du vert clair (valeur HSV)"""
        if image is None:
            return False
            
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Plage de vert clair (à ajuster selon votre jeu)
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([80, 255, 255])
        
        mask = cv2.inRange(hsv, lower_green, upper_green)
        green_percentage = np.sum(mask > 0) / (image.shape[0] * image.shape[1])
        
        print(f"Pourcentage vert: {green_percentage:.2%}")
        return green_percentage > 0.6  # Si >60% de vert

    def wait_for_loading(self):
    """Combine OCR et détection de couleur"""
    print("Début du processus de chargement...")
    
    for attempt in range(1, self.max_attempts + 1):
        try:
            print(f"Tentative {attempt}/{self.max_attempts}")
            screenshot = self.phone.capture_screen()
            
            if screenshot is None:
                continue
                
            # Méthode 1: Détection OCR
            percentage = self.detect_loading_percentage(screenshot)
            if percentage == 100:
                print("✅ Chargement complet (OCR)")
                return 1
                
            # Méthode 2: Détection de couleur
            if self.is_green_loaded(screenshot):
                print("✅ Chargement complet (Couleur verte)")
                return 1
                
            time.sleep(self.check_interval)
            
        except Exception as e:
            print(f"Erreur: {str(e)}")
    
    print("❌ Échec du chargement")
    return 0

if __name__ == "__main__":
    loader = GameLoader()
    game_loaded = loader.wait_for_loading()
    
    if game_loaded == 1:
        print("Le jeu est prêt! game_loaded = 1")
    else:
        print("Échec du chargement")