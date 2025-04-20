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
        """Déverrouillage robuste pour Huawei/Android"""
        try:
            # 1. Allumer l'écran
            subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_POWER"], 
                        timeout=2, check=True)
            time.sleep(0.5)
            
            # 2. Glisser pour déverrouiller (coordonnées pour Huawei)
            subprocess.run(["adb", "shell", "input", "swipe", "300", "1200", "300", "400", "200"],
                        timeout=2, check=True)
            time.sleep(1)
            
            # 3. Entrer le code PIN si nécessaire (à configurer)
            # subprocess.run(["adb", "shell", "input", "text", "1234"], timeout=2)
            # time.sleep(0.5)
            
            print("✅ Déverrouillage réussi")
            return True
            
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout déverrouillage - Réessayer")
        except Exception as e:
            print(f"⚠️ Erreur déverrouillage: {str(e)}")
        
        return False

    def check_phone_state(self):
        """Vérifie si l'appareil est verrouillé"""
        try:
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "window"],
                stdout=subprocess.PIPE,
                text=True,
                timeout=5
            )
            return "mDreamingLockscreen=true" in result.stdout
        except:
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
        """Processus complet avec vérification d'état"""
        print("=== Vérification initiale ===")
        
        # Vérification verrouillage
        if self.check_phone_state():
            print("📱 Appareil verrouillé - Déverrouillage...")
            if not self.unlock_device():
                print("❌ Impossible de déverrouiller")
                return 0
            time.sleep(3)  # Latence post-déverrouillage
        
        # Vérification jeu déjà lancé
        screenshot = self.phone.capture_screen()
        if self.check_pixel_color(screenshot):
            print("✅ Jeu déjà en cours")
            return 1
        
        # Lancement du jeu
        print("🚀 Lancement du jeu...")
        try:
            subprocess.run(
                ["adb", "shell", "monkey", "-p", self.game_package, "1"],
                check=True,
                timeout=15,
                stdout=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"⚠️ Échec lancement: {str(e)}")
            return 0
        
        # Attente chargement
        print("⏳ Attente du chargement...")
        for attempt in range(1, 21):
            screenshot = self.phone.capture_screen()
            if self.check_pixel_color(screenshot):
                print(f"✅ Jeu chargé (tentative {attempt})")
                return 1
                
            if self.check_phone_state():
                print("📱 Re-verrouillage détecté!")
                self.unlock_device()
                
            print(f"⌛ Tentative {attempt}/20")
            time.sleep(3)
        
        print("❌ Timeout de chargement")
        return 0

if __name__ == "__main__":
    print("Démarrage du système...")
    loader = GameLoader()
    
    if loader.wait_for_loading() == 1:
        print("STATUS: PRÊT À JOUER")
    else:
        print("STATUS: ÉCHEC - Vérifiez manuellement")