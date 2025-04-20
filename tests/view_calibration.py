import cv2
import numpy as np
import subprocess
import time
import json
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class ViewMode:
    name: str
    signature: Dict[str, List[int]]  # {"zone1": [x,y,r,g,b,tolerance], ...}

class AndroidViewDetector:
    def __init__(self, device_serial: str = None):
        self.device_serial = device_serial or self._detect_connected_device()
        self.modes = self._load_view_modes()
        self._validate_connection()

    def _detect_connected_device(self) -> str:
        """Trouve automatiquement le device Android connecté en USB"""
        try:
            result = subprocess.run(['adb', 'devices'], 
                                 capture_output=True, 
                                 text=True,
                                 check=True)
            devices = [line.split('\t')[0] 
                     for line in result.stdout.splitlines() 
                     if '\tdevice' in line]
            if not devices:
                raise ConnectionError("Aucun appareil Android détecté via USB")
            return devices[0]
        except subprocess.CalledProcessError as e:
            raise ConnectionError(f"Erreur ADB: {e.stderr}") from e

    def _validate_connection(self):
        """Vérifie que la connexion ADB fonctionne"""
        try:
            subprocess.run(['adb', '-s', self.device_serial, 'shell', 'echo', 'test'],
                         check=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise ConnectionError(f"Échec de communication avec l'appareil: {e.stderr.decode()}")

    def _load_view_modes(self) -> Dict[str, ViewMode]:
        """Charge les signatures des modes de vue depuis un fichier JSON"""
        try:
            with open('view_modes.json') as f:
                data = json.load(f)
                return {k: ViewMode(name=k, signature=v) for k,v in data.items()}
        except FileNotFoundError:
            return {
                'ville': ViewMode('ville', {'top_right': [2242,703,105,178,124,15]}),
                'alentour': ViewMode('alentour', {'middle_left': [1604,630,40,120,178,10]})
            }

    def capture_screen(self) -> Optional[np.ndarray]:
        """Capture d'écran robuste avec vérification d'erreur"""
        try:
            result = subprocess.run(['adb', '-s', self.device_serial, 'exec-out', 'screencap', '-p'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   check=True)
            
            img_array = np.frombuffer(result.stdout, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Échec du décodage de l'image")
            return img
        except (subprocess.CalledProcessError, ValueError) as e:
            print(f"Erreur capture: {str(e)}")
            return None

    def detect_current_view(self, img: np.ndarray) -> Optional[str]:
        """Détecte le mode de vue actuel avec gestion d'erreur"""
        if img is None:
            raise ValueError("Image non fournie pour la détection")
        
        best_match = None
        best_score = 0
        
        for mode_name, mode in self.modes.items():
            total_matches = 0
            required_matches = len(mode.signature)
            
            for zone, (x, y, r, g, b, tol) in mode.signature.items():
                try:
                    if y >= img.shape[0] or x >= img.shape[1]:
                        continue
                        
                    pixel = img[y, x]
                    if np.all(np.abs(pixel - [b,g,r]) <= tol):  # OpenCV utilise BGR
                        total_matches += 1
                except Exception as e:
                    print(f"Erreur analyse zone {zone}: {str(e)}")
                    continue
            
            match_ratio = total_matches / required_matches
            if match_ratio > 0.8 and match_ratio > best_score:  # 80% des zones correspondent
                best_score = match_ratio
                best_match = mode_name
                
        return best_match

    def interactive_calibration(self):
        """Mode calibration pas-à-pas"""
        print("Début de la calibration interactive...")
        mode_name = input("Nom du nouveau mode: ")
        
        print("Capture des zones caractéristiques...")
        input("Placez-vous dans le mode puis appuyez sur Entrée")
        
        signature = {}
        img = self.capture_screen()
        if img is None:
            return
            
        cv2.imshow('Calibration', img)
        print("Cliquez sur les zones caractéristiques (ESC pour terminer)")
        
        points = []
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                color = img[y,x]
                print(f"Zone {len(points)+1}: ({x},{y}) - Couleur {color}")
                points.append((x, y, color[2], color[1], color[0], 10))  # (x,y,r,g,b,tol)
                cv2.circle(img, (x,y), 5, (0,255,0), -1)
                cv2.imshow('Calibration', img)
        
        cv2.setMouseCallback('Calibration', mouse_callback)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        for i, (x,y,r,g,b,tol) in enumerate(points, 1):
            signature[f'zone{i}'] = [x,y,r,g,b,tol]
        
        self.modes[mode_name] = ViewMode(mode_name, signature)
        self._save_modes()
        print(f"Mode '{mode_name}' enregistré avec {len(points)} zones")

    def _save_modes(self):
        """Sauvegarde les modes dans un fichier JSON"""
        with open('view_modes.json', 'w') as f:
            json.dump({k: v.signature for k,v in self.modes.items()}, f, indent=2)

if __name__ == "__main__":
    try:
        detector = AndroidViewDetector("EML-L09")  # Utilisez None pour auto-détection
        
        while True:
            print("\nOptions:")
            print("1. Détecter le mode actuel")
            print("2. Calibrer un nouveau mode")
            print("3. Quitter")
            
            choice = input("Votre choix: ")
            
            if choice == '1':
                print("Capture en cours...")
                img = detector.capture_screen()
                if img is not None:
                    mode = detector.detect_current_view(img)
                    print(f"\nMode détecté: {mode if mode else 'Inconnu'}")
            
            elif choice == '2':
                detector.interactive_calibration()
            
            elif choice == '3':
                break
                
    except Exception as e:
        print(f"Erreur critique: {str(e)}")
        input("Appuyez sur Entrée pour quitter...")