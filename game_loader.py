import cv2
import numpy as np
import time
from phone_controller import PhoneController

class GameLoader:
    def __init__(self):
        self.phone = PhoneController()
        self.max_attempts = 8  # Tentatives avant lancement
        self.check_interval = 1.5
        
        # Configuration pixel
        self.pixel_x = 171
        self.pixel_y = 947
        self.expected_color = np.array([248, 255, 255])  # BGR
        self.color_tolerance = 15  # Marge élargie
        
        # Configuration jeu
        self.game_package = "com.lilithgame.roc.gp"  # Package ROK

    def check_pixel_color(self, image):
        """Vérifie la couleur du pixel avec tolérance"""
        try:
            actual_color = image[self.pixel_y, self.pixel_x]
            return np.all(np.abs(actual_color - self.expected_color) <= self.color_tolerance)
        except:
            return False

    def launch_game(self):
        """Lance le jeu via ADB si pas détecté"""
        print("Lancement du jeu...")
        try:
            subprocess.run(
                ["adb", "shell", "monkey", "-p", self.game_package, "-c", "android.intent.category.LAUNCHER", "1"],
                check=True,
                timeout=10
            )
            time.sleep(10)  # Temps de chargement initial
            return True
        except Exception as e:
            print(f"Échec lancement: {e}")
            return False

    def wait_for_loading(self):
        """Processus complet avec lancement automatique"""
        print("=== Vérification état du jeu ===")
        
        # Phase 1: Vérification rapide
        for attempt in range(1, self.max_attempts + 1):
            screenshot = self.phone.capture_screen()
            if screenshot is None:
                continue
                
            if self.check_pixel_color(screenshot):
                print(f"✅ Jeu déjà en cours (tentative {attempt})")
                return 1
                
            time.sleep(self.check_interval)
        
        # Phase 2: Lancement si non détecté
        print("Jeu non détecté - tentative de lancement...")
        if self.launch_game():
            # Phase 3: Attente post-lancement
            for wait_attempt in range(10):  # 10 x 3s = 30s max
                screenshot = self.phone.capture_screen()
                if screenshot and self.check_pixel_color(screenshot):
                    print("✅ Jeu lancé avec succès")
                    return 1
                time.sleep(3)
        
        print("❌ Échec de chargement")
        return 0

if __name__ == "__main__":
    loader = GameLoader()
    if loader.wait_for_loading() == 1:
        print("STATUS: Prêt à jouer!")
    else:
        print("STATUS: Échec - vérifiez manuellement")