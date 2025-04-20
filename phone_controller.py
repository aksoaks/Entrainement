import subprocess
import re
import cv2
import numpy as np
import os

class PhoneController:
    """Classe pour contrôler un appareil Android via ADB"""
    
    def __init__(self, device_id=None):
        self.device_id = device_id
        self.adb_prefix = ["adb"] if not device_id else ["adb", "-s", device_id]
        self._check_adb_installation()
        self.check_connection()
        self.resolution = self.get_screen_resolution()
        self.density = self.get_screen_density()
        self.orientation = self.get_screen_orientation()
        self.setup_touch_parameters()

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
        """Vérifie la connexion au périphérique"""
        try:
            result = subprocess.run(
                self.adb_prefix + ["get-state"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            if "device" not in result.stdout.strip():
                raise RuntimeError("Périphérique non connecté ou non autorisé")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erreur de connexion ADB: {e.stderr}")

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
        """Capture l'écran du téléphone et retourne l'image"""
        try:
            # Supprimer l'ancien fichier s'il existe
            if os.path.exists(filename):
                os.remove(filename)
                
            # Nouvelle capture
            with open(filename, 'wb') as f:
                subprocess.run(
                    self.adb_prefix + ["exec-out", "screencap", "-p"],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    check=True
                )
            
            # Lire et retourner l'image
            img = cv2.imread(filename)
            if img is None:
                raise ValueError("Impossible de lire l'image capturée")
            return img
            
        except Exception as e:
            print(f"Erreur de capture: {str(e)}")
            # Retourne une image noire en cas d'échec
            return np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

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