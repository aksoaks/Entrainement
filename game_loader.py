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
        """Vérifie la couleur du pixel avec tolérance"""
        if image is None:
            return False
        try:
            actual_color = image[self.pixel_y, self.pixel_x]
            print(f"Couleur détectée: {actual_color} | Attendue: {self.expected_color}")
            return np.all(np.abs(actual_color - self.expected_color) <= self.color_tolerance)
        except:
            return False

    def unlock_device(self):
        """Déverrouille l'appareil Android"""
        print("🔓 Tentative de déverrouillage...")
        try:
            # Allume l'écran
            subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_POWER"], timeout=5)
            time.sleep(1)
            
            # Glisse pour déverrouiller (adaptez les coordonnées si nécessaire)
            subprocess.run(["adb", "shell", "input", "swipe", "300", "1000", "300", "500"], timeout=5)
            time.sleep(1)
            
            # Entrée du code PIN (si configuré - à personnaliser)
            # subprocess.run(["adb", "shell", "input", "text", "1234"], timeout=5)
            # time.sleep(1)
            
            print("✅ Déverrouillage tenté")
            return True
        except Exception as e:
            print(f"⚠️ Échec déverrouillage: {e}")
            return False

    def launch_game(self):
        """Lance le jeu avec gestion du verrouillage"""
        # Vérifie si l'appareil est verrouillé
        try:
            lock_state = subprocess.run(
                ["adb", "shell", "dumpsys", "window"],
                stdout=subprocess.PIPE,
                text=True
            ).stdout
            
            if "mDreamingLockscreen=true" in lock_state:
                self.unlock_device()
                time.sleep(3)  # Attente après déverrouillage
        except:
            pass
            
        # Lancement du jeu
        print("🚀 Lancement du jeu...")
        start_time = time.time()
        try:
            subprocess.run(
                ["adb", "shell", "monkey", "-p", self.game_package, "-c", "android.intent.category.LAUNCHER", "1"],
                check=True,
                timeout=15
            )
            return start_time
        except Exception as e:
            print(f"⚠️ Erreur lancement: {e}")
            return None

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