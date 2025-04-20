import cv2
import numpy as np
import time
import subprocess
from phone_controller import PhoneController

class GameLoader:
    def __init__(self):
        self.phone = PhoneController()
        self.post_launch_attempts = 20
        self.check_interval = 3
        self.pixel_x = 171
        self.pixel_y = 947
        self.expected_color = np.array([255, 255, 251])
        self.color_tolerance = 5
        self.game_package = "com.lilithgame.roc.gp"

    def check_pixel_color(self, image):
        if image is None or np.mean(image) < 10:  # Détection écran noir
            print("📱 Écran verrouillé/éteint")
            return False
        try:
            actual_color = image[self.pixel_y, self.pixel_x]
            print(f"Couleur détectée: {actual_color} | Attendue: {self.expected_color}")
            return np.all(np.abs(actual_color - self.expected_color) <= self.color_tolerance)
        except:
            return False

    def unlock_device(self):
        """Déverrouillage optimisé en une étape"""
        try:
            # Unlock combo (power + swipe rapide)
            subprocess.run([
                "adb", "shell", "input", "keyevent", "KEYCODE_WAKEUP",
                "&&", "input", "swipe", "500", "1500", "500", "500", "100"
            ], timeout=3)
            time.sleep(1.5)  # Temps réduit
            print("🔓 Déverrouillage instantané")
            return True
        except Exception as e:
            print(f"⚠️ Échec déverrouillage: {e}")
            return False

    def launch_game(self):
    """Lancement silencieux avec timeout réduit"""
    try:
        print("🚀 Lancement en cours...")
        result = subprocess.run(
            ["adb", "shell", "monkey", "-p", self.game_package, "1"],
            stdout=subprocess.DEVNULL,  # Supprime les logs verbeux
            stderr=subprocess.PIPE,
            timeout=10
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout lancement")
        return False

    def wait_for_loading(self):
        """Processus complet avec déverrouillage"""
        print("=== Vérification du jeu ===")
        
        # Vérification unique
        screenshot = self.phone.capture_screen()
        if screenshot is not None and self.check_pixel_color(screenshot):
            print("✅ Jeu déjà en cours")
            return 1
        
        # Lancement + attente
        launch_time = self.launch_game()
        if launch_time is None:
            return 0
            
        print("⏳ Attente du chargement...")
        for attempt in range(1, self.post_launch_attempts + 1):
            screenshot = self.phone.capture_screen()
            if screenshot is not None and self.check_pixel_color(screenshot):
                load_time = time.time() - launch_time
                print(f"✅ Jeu chargé en {load_time:.1f}s")
                return 1
                
            print(f"⌛ Tentative {attempt}/{self.post_launch_attempts}")
            time.sleep(self.check_interval)
        
        print("❌ Timeout après lancement")
        return 0

if __name__ == "__main__":
    print("Démarrage du système...")
    loader = GameLoader()
    
    if loader.wait_for_loading() == 1:
        print("STATUS: PRÊT À JOUER")
    else:
        print("STATUS: ÉCHEC - Vérifiez manuellement")