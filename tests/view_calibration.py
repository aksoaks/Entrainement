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
        """Version avec logging détaillé"""
            print("\nDébut de la détection...")
            
            best_match = None
            best_score = 0
            
            for mode_name, mode in self.modes.items():
                print(f"\nVérification du mode: {mode_name}")
                total_matches = 0
                
                for zone, params in mode.signature.items():
                    x, y, r, g, b, tol = params
                    try:
                        if y >= img.shape[0] or x >= img.shape[1]:
                            print(f"Zone {zone} hors limites - Image: {img.shape}")
                            continue
                        
                        pixel = img[y, x]
                        diff = np.abs(pixel - [b, g, r])
                        print(f"Zone {zone} ({x},{y}) - Attendu: {[r,g,b]} | Réel: {pixel[::-1]} | Diff: {diff}")
                        
                        if np.all(diff <= tol):
                            total_matches += 1
                            print("→ Correspondance!")
                        else:
                            print(f"→ Écart trop important (tolérance: {tol})")
                            
                    except Exception as e:
                        print(f"Erreur zone {zone}: {str(e)}")
                
                match_ratio = total_matches / len(mode.signature)
                print(f"Score {mode_name}: {match_ratio:.2f}")
                
                if match_ratio > 0.7 and match_ratio > best_score:
                    best_score = match_ratio
                    best_match = mode_name
            
            print(f"\nDétection terminée - Meilleur match: {best_match} (score: {best_score:.2f})")
            return best_match if best_score > 0.7 else None

    def interactive_calibration(self):
        """Calibration interactive avec gestion d'état"""
        print("\n=== Mode Calibration ===")
        mode_name = input("Nom du nouveau mode: ").strip()
        
        print("Capture de l'écran de référence...")
        img = self.capture_screen()
        if img is None:
            print("Échec de la capture - vérifiez la connexion USB")
            return
        
        clone = img.copy()
        points = []
        window_name = f"Calibration - {mode_name} (CLIC=zone, C=Annuler, S=Sauver)"
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal clone
            if event == cv2.EVENT_LBUTTONDOWN:
                color = clone[y, x]
                print(f"Zone {len(points)+1}: ({x},{y}) | RGB: {color[::-1]}")
                points.append((x, y, color[2], color[1], color[0], 10))
                cv2.circle(clone, (x, y), 5, (0, 255, 0), -1)
                cv2.imshow(window_name, clone)
        
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, mouse_callback)
        cv2.imshow(window_name, clone)
        
        print("Instructions:")
        print("- Cliquez sur les zones caractéristiques")
        print("- 'S': Sauvegarder et quitter")
        print("- 'C': Annuler et recommencer")
        
        while True:
            key = cv2.waitKey(20) & 0xFF
            if key == ord('s'):
                break
            elif key == ord('c'):
                points.clear()
                clone = img.copy()
                cv2.imshow(window_name, clone)
                print("Calibration réinitialisée")
        
        cv2.destroyAllWindows()
        
        if points:
            self.modes[mode_name] = ViewMode(
                name=mode_name,
                signature={f"zone_{i}": list(p) for i, p in enumerate(points, 1)}
            )
            self._save_modes()
            print(f"\nMode '{mode_name}' sauvegardé avec {len(points)} zones")
            print("Vérification du fichier view_modes.json...")
            print(json.dumps(self.modes[mode_name].signature, indent=2))
        else:
            print("Aucune zone enregistrée - calibration annulée")

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