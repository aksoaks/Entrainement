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
    def __init__(self):
        self.device_serial = self._get_device_serial()
        self.modes = self._load_view_modes()
        self._test_connection()

    def _get_device_serial(self) -> str:
        """Récupère automatiquement le numéro de série du device connecté"""
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

    def _test_connection(self):
        """Vérifie que la connexion ADB fonctionne"""
        try:
            subprocess.run(['adb', '-s', self.device_serial, 'shell', 'echo', 'test'],
                         check=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
            print(f"Connecté à l'appareil: {self.device_serial}")
        except subprocess.CalledProcessError as e:
            raise ConnectionError(f"Échec de communication: {e.stderr.decode()}")

    def capture_screen(self) -> Optional[np.ndarray]:
        """Capture d'écran robuste avec vérification"""
        try:
            result = subprocess.run(
                ['adb', '-s', self.device_serial, 'exec-out', 'screencap', '-p'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            img = cv2.imdecode(np.frombuffer(result.stdout, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Échec du décodage de l'image")
            return img
        except Exception as e:
            print(f"Erreur capture: {str(e)}")
            return None

    def detect_view_mode(self, img: np.ndarray) -> Optional[str]:
        """Détecte le mode de vue actuel"""
        if img is None:
            return None
            
        best_match = None
        best_score = 0
        
        for mode_name, mode in self.modes.items():
            matches = 0
            required = len(mode.signature)
            
            for zone, (x, y, r, g, b, tol) in mode.signature.items():
                try:
                    if (y < img.shape[0] and x < img.shape[1] and 
                        np.all(np.abs(img[y,x] - [b,g,r]) <= tol)):
                        matches += 1
                except:
                    continue
            
            if matches/required > 0.7 and matches > best_score:
                best_score = matches
                best_match = mode_name
                
        return best_match

    def interactive_calibration(self):
        """Mode calibration interactif"""
        print("\n=== Mode Calibration ===")
        mode_name = input("Nom du nouveau mode: ").strip()
        
        print("Préparez l'écran puis appuyez sur Entrée...")
        input()
        
        img = self.capture_screen()
        if img is None:
            return
            
        cv2.imshow("Calibration - Cliquez sur les zones caractéristiques", img)
        points = []
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                color = img[y,x]
                print(f"Zone {len(points)+1}: ({x},{y}) - Couleur {color[::-1]} (RGB)")
                points.append((x, y, color[2], color[1], color[0], 10))
                cv2.circle(img, (x,y), 5, (0,255,0), -1)
                cv2.imshow("Calibration - Cliquez sur les zones caractéristiques", img)
        
        cv2.setMouseCallback("Calibration - Cliquez sur les zones caractéristiques", mouse_callback)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        if points:
            self.modes[mode_name] = ViewMode(
                name=mode_name,
                signature={f"zone{i}": list(p) for i,p in enumerate(points, 1)}
            )
            self._save_modes()
            print(f"Mode '{mode_name}' enregistré avec {len(points)} zones")
        else:
            print("Aucune zone enregistrée")

    def _load_view_modes(self) -> Dict[str, ViewMode]:
        """Charge les signatures des modes"""
        try:
            with open('view_modes.json') as f:
                data = json.load(f)
                return {k: ViewMode(k, v) for k,v in data.items()}
        except FileNotFoundError:
            return {
                'ville': ViewMode('ville', {'zone1': [2242,703,105,178,124,15]}),
                'alentour': ViewMode('alentour', {'zone1': [1604,630,40,120,178,10]})
            }

    def _save_modes(self):
        """Sauvegarde les modes dans un fichier JSON"""
        with open('view_modes.json', 'w') as f:
            json.dump(
                {k: v.signature for k,v in self.modes.items()},
                f,
                indent=2
            )

def main():
    try:
        print("Initialisation du détecteur...")
        detector = AndroidViewDetector()
        
        while True:
            print("\n=== Menu Principal ===")
            print("1. Détecter le mode actuel")
            print("2. Calibrer un nouveau mode")
            print("3. Quitter")
            
            choice = input("Choix: ").strip()
            
            if choice == '1':
                print("Capture en cours...")
                img = detector.capture_screen()
                if img is not None:
                    mode = detector.detect_view_mode(img)
                    print(f"\nMode détecté: {mode if mode else 'Inconnu'}")
            
            elif choice == '2':
                detector.interactive_calibration()
            
            elif choice == '3':
                break
                
    except Exception as e:
        print(f"\nERREUR: {str(e)}")
    finally:
        input("Appuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main()