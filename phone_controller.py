import subprocess
import re
import cv2
import numpy as np
import os

class PhoneController:
    """Classe pour contrôler un appareil Android via ADB"""
    
    def __init__(self, device_id=None):
        self.adb_prefix = ["adb"] if not device_id else ["adb", "-s", device_id]
        self._check_adb_installation()
        self.check_connection()
        self.resolution = self.get_screen_resolution()
        self.density = self.get_screen_density()
        self.orientation = self.get_screen_orientation()
        self.setup_touch_parameters()

    def check_connection(self):
        """Vérification améliorée"""
        try:
            result = subprocess.run(self.adb_prefix + ["devices"],
                                stdout=subprocess.PIPE,
                                text=True,
                                check=True)
            print("Appareils connectés:\n", result.stdout)  # Debug
            if "device" not in result.stdout:
                raise RuntimeError("Aucun appareil autorisé")
        except Exception as e:
            print(f"ERREUR ADB: {str(e)}")
            return False
        return True

    def run_adb_command(self, command):
        """Exécute une commande ADB et retourne le résultat"""
        try:
            result = subprocess.run(
                self.adb_prefix + ["shell", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Échec commande ADB: {str(e)}")
            return ""

    def _check_adb_installation(self):
        """Vérifie si ADB est installé et accessible"""
        try:
            subprocess.run(
                ["adb", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("ADB n'est pas installé ou n'est pas dans le PATH")

    def check_connection(self):
        """Vérification améliorée de la connexion"""
        try:
            # Commande plus fiable
            result = subprocess.run(
                self.adb_prefix + ["shell", "getprop", "ro.product.model"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Erreur ADB: {result.stderr.strip()}")
                
            print(f"Appareil connecté: {result.stdout.strip()}")
            return True
        except Exception as e:
            print(f"Échec vérification connexion: {str(e)}")
            return False            

    def get_screen_resolution(self):
        """Récupère la résolution de l'écran"""
        try:
            result = subprocess.run(
                self.adb_prefix + ["shell", "wm", "size"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            match = re.search(r"(\d+)x(\d+)", result.stdout)
            if match:
                return (int(match.group(1)), int(match.group(2)))
            raise RuntimeError("Impossible de parser la résolution")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erreur lors de la récupération de la résolution: {e.stderr}")

    def get_screen_density(self):
        """Récupère la densité de l'écran"""
        try:
            result = subprocess.run(
                self.adb_prefix + ["shell", "wm", "density"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            match = re.search(r"(\d+)", result.stdout)
            if match:
                return int(match.group(1))
            raise RuntimeError("Impossible de parser la densité")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erreur lors de la récupération de la densité: {e.stderr}")

    def get_screen_orientation(self):
        """Récupère l'orientation de l'écran"""
        try:
            result = subprocess.run(
                self.adb_prefix + ["shell", "dumpsys", "input"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            if "SurfaceOrientation: 0" in result.stdout:
                return 0  # Portrait
            elif "SurfaceOrientation: 1" in result.stdout:
                return 1  # Paysage
            else:
                return 0  # Par défaut portrait
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erreur lors de la récupération de l'orientation: {e.stderr}")

    def setup_touch_parameters(self):
        """Configure les paramètres de toucher en fonction de la densité"""
        self.touch_multiplier = self.density / 160  # Densité de référence: 160dpi (mdpi)

    def print_debug_info(self):
        """Affiche les informations de débogage"""
        print(f"Résolution: {self.resolution[0]}x{self.resolution[1]}")
        print(f"Densité: {self.density}dpi")
        print(f"Orientation: {'Paysage' if self.orientation else 'Portrait'}")
        print(f"Multiplicateur de toucher: {self.touch_multiplier:.2f}")

    def calibrate(self):
        """Calibration de base"""
        print("Calibration en cours...")
        sleep(1)  # Simulation de calibration

    def capture_screen(self, filename="screen.png"):
        """Capture améliorée avec vérification"""
        try:
            # Nouvelle méthode plus fiable
            result = subprocess.run(
                self.adb_prefix + ["exec-out", "screencap -p"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=10
            )
            
            img_array = np.frombuffer(result.stdout, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Données d'image corrompues")
            
            cv2.imwrite(filename, img)
            return img
            
        except subprocess.TimeoutExpired:
            print("Timeout capture - Redémarrage ADB...")
            self.restart_adb()
            return None
        except Exception as e:
            print(f"Erreur capture: {str(e)}")
            return None

    def restart_adb(self):
        """Redémarre le serveur ADB"""
        subprocess.run(["adb", "kill-server"])
        subprocess.run(["adb", "start-server"])
        time.sleep(2)
        
    def capture_and_show(self, scale_factor=0.5):
        """Capture et affiche l'écran avec redimensionnement"""
        try:
            img = self.capture_screen()
            if img is None:
                return

            # Redimensionnement
            height, width = img.shape[:2]
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            resized_img = cv2.resize(img, (new_width, new_height))
            
            # Affichage
            cv2.imshow(f"Capture ({new_width}x{new_height})", resized_img)
            cv2.waitKey(3000)
            
        except Exception as e:
            print(f"Erreur d'affichage: {str(e)}")
        finally:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        phone = PhoneController()
        phone.print_debug_info()
        phone.calibrate()
        
        # Soit utiliser capture_and_show()
        phone.capture_and_show(scale_factor=0.5)
        
        # Soit faire manuellement:
        # img = phone.capture_screen()
        # if img is not None:
        #     resized = cv2.resize(img, (0,0), fx=0.5, fy=0.5)
        #     cv2.imshow("Capture", resized)
        #     cv2.waitKey(3000)
        
    except Exception as e:
        print(f"ERREUR: {str(e)}")
    finally:
        cv2.destroyAllWindows()