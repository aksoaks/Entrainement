import cv2
import numpy as np
import time
import subprocess
from phone_controller import PhoneController

class GameLoader:
    def __init__(self):
        self.phone = PhoneController()
        self.max_attempts = 5  # Tentatives avant lancement
        self.post_launch_attempts = 10  # Tentatives après lancement
        self.check_interval = 2  # Intervalle de vérification
        
        # Configuration pixel
        self.pixel_x = 171
        self.pixel_y = 947
        self.expected_color = np.array([255, 255, 251])  # BGR (valeur corrigée)
        self.color_tolerance = 20  # Marge élargie
        
        # Configuration jeu
        self.game_package = "com.lilithgame.roc.gp"

    def check_pixel_color(self, image):
        """Vérifie la couleur du pixel avec tolérance"""
        if image is None:
            return False
            
        try:
            # Vérifie que le pixel est dans l'image
            if self.pixel_y >= image.shape[0] or self.pixel_x >= image.shape[1]:
                print("Coordonnées pixel hors limites")
                return False
                
            actual_color = image[self.pixel_y, self.pixel_x]
            print(f"Détection pixel: {actual_color} vs {self.expected_color}")
            return np.all(np.abs(actual_color - self.expected_color) <= self.color_tolerance)
        except Exception as e:
            print(f"Erreur vérification pixel: {e}")
            return False

    def launch_game(self):
        """Lance le jeu via ADB"""
        print("Tentative de lancement du jeu...")
        try:
            # Commande ADB pour lancer le jeu
            result = subprocess.run(
                ["adb", "shell", "monkey", "-p", self.game_package, "-c", "android.intent.category.LAUNCHER", "1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15
            )
            if result.returncode == 0:
                print("Lancement réussi, attente du chargement...")
                return True
            print("Échec du lancement")
            return False
        except subprocess.TimeoutExpired:
            print("Timeout lors du lancement")
            return False
        except Exception as e:
            print(f"Exception lors du lancement: {e}")
            return False

    def wait_for_loading(self):
        """Processus complet avec gestion d'erreurs améliorée"""
        print("=== Initialisation du vérificateur de jeu ===")
        
        # Phase 1: Vérification de l'état actuel
        print("Vérification si le jeu est déjà lancé...")
        for attempt in range(1, self.max_attempts + 1):
            try:
                screenshot = self.phone.capture_screen()
                if screenshot is not None and self.check_pixel_color(screenshot):
                    print(f"✅ Jeu détecté (tentative {attempt})")
                    return 1
                
                print(f"Jeu non détecté (tentative {attempt}/{self.max_attempts})")
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"Erreur lors de la vérification: {e}")
                time.sleep(self.check_interval)
        
        # Phase 2: Lancement du jeu
        if not self.launch_game():
            print("❌ Impossible de lancer le jeu")
            return 0
        
        # Phase 3: Vérification post-lancement
        print("Vérification du chargement après lancement...")
        for attempt in range(1, self.post_launch_attempts + 1):
            try:
                screenshot = self.phone.capture_screen()
                if screenshot is not None and self.check_pixel_color(screenshot):
                    print(f"✅ Jeu chargé avec succès (tentative {attempt})")
                    return 1
                
                print(f"En attente... ({attempt}/{self.post_launch_attempts})")
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"Erreur vérification post-lancement: {e}")
                time.sleep(self.check_interval)
        
        print("❌ Timeout - Jeu non chargé")
        return 0

if __name__ == "__main__":
    print("Démarrage du système...")
    loader = GameLoader()
    result = loader.wait_for_loading()
    
    if result == 1:
        print("=== PRÊT À JOUER ===")
    else:
        print("=== ÉCHEC - VÉRIFIEZ MANUEL ===")