import cv2
import numpy as np
import time
from phone_controller import PhoneController

class GameLoader:
    def __init__(self):
        self.phone = PhoneController()
        self.max_attempts = 5  # Réduit car vérification instantanée
        self.check_interval = 1
        
        # Coordonnées et couleur du pixel à vérifier
        self.pixel_x = 171
        self.pixel_y = 947
        self.expected_color = np.array([248, 255, 255])  # BGR
        self.color_tolerance = 10  # Marge d'erreur

    def check_pixel_color(self, image):
        """Vérifie si le pixel cible a la bonne couleur"""
        try:
            # Vérifie que les coordonnées sont dans l'image
            height, width = image.shape[:2]
            if self.pixel_x >= width or self.pixel_y >= height:
                print("Coordonnées pixel invalides")
                return False
                
            # Récupère la couleur du pixel
            actual_color = image[self.pixel_y, self.pixel_x]
            
            # Calcule la différence avec la couleur attendue
            color_diff = np.abs(actual_color - self.expected_color)
            
            print(f"Couleur réelle: {actual_color} | Attendue: {self.expected_color}")
            
            # Vérifie si dans la tolérance
            return np.all(color_diff <= self.color_tolerance)
            
        except Exception as e:
            print(f"Erreur vérification pixel: {e}")
            return False

    def wait_for_loading(self):
        """Attend que le jeu soit chargé en vérifiant le pixel"""
        print("Début vérification chargement...")
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                # Capture écran
                screenshot = self.phone.capture_screen()
                if screenshot is None:
                    print("Échec capture écran")
                    continue
                
                # Vérification pixel
                if self.check_pixel_color(screenshot):
                    print("✅ Pixel correct détecté - Jeu chargé")
                    return 1
                    
                print(f"Tentative {attempt}/{self.max_attempts} - Jeu non chargé")
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"Erreur: {e}")
                continue
                
        print("❌ Timeout - Jeu non chargé")
        return 0

if __name__ == "__main__":
    loader = GameLoader()
    if loader.wait_for_loading() == 1:
        print("Jeu prêt!")
    else:
        print("Échec détection")