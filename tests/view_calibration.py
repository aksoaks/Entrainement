import cv2
import numpy as np
import os
import time
from collections import defaultdict

class ViewDetector:
    def __init__(self, device_serial):
        self.device_serial = device_serial
        self.reference_data = defaultdict(dict)
        self.load_references()
        
    def capture_via_usb(self):
        """Capture d'écran via USB avec ADB"""
        timestamp = str(int(time.time()))
        img_path = f"capture_{timestamp}.png"
        
        # Commande ADB en mode USB
        os.system(f"adb -s {self.device_serial} exec-out screencap -p > {img_path}")
        
        img = cv2.imread(img_path)
        os.remove(img_path)  # Nettoyage
        return img

    def load_references(self):
        """Charge les signatures de référence des modes"""
        # Exemple de structure à compléter avec vos données
        self.reference_data = {
            'ville': {
                'zones': [(2242,703), (2207,702)],
                'couleurs': {
                    (2242,703): [105, 178, 124],
                    (2207,702): [90, 175, 150]
                },
                'seuil': 15  # Tolérance couleur
            },
            'alentour': {
                'zones': [(1604,630), (1598,630)],
                'couleurs': {
                    (1604,630): [40, 120, 178],
                    (1598,630): [36, 116, 181]
                },
                'seuil': 10
            }
        }

    def detect_mode(self, img):
        """Détecte le mode actuel par comparaison"""
        best_match = None
        lowest_diff = float('inf')
        
        for mode, data in self.reference_data.items():
            total_diff = 0
            valid_points = 0
            
            for coord, ref_color in data['couleurs'].items():
                x, y = coord
                if y < img.shape[0] and x < img.shape[1]:
                    pixel = img[y, x]
                    diff = np.sqrt(np.sum((pixel - ref_color)**2))
                    if diff <= data['seuil']:
                        total_diff += diff
                        valid_points += 1
            
            if valid_points > 0:
                avg_diff = total_diff / valid_points
                if avg_diff < lowest_diff:
                    lowest_diff = avg_diff
                    best_match = mode
        
        return best_match if lowest_diff < 50 else None  # Seuil global

    def calibrate_mode(self, mode_name, samples=3):
        """Calibration d'un nouveau mode"""
        print(f"\nCalibration du mode {mode_name}...")
        input("Placez-vous dans le mode puis appuyez sur Entrée")
        
        color_samples = defaultdict(list)
        
        for _ in range(samples):
            img = self.capture_via_usb()
            if img is None:
                continue
                
            for x, y in self.reference_data['ville']['zones']:  # Zones communes
                if y < img.shape[0] and x < img.shape[1]:
                    color_samples[(x,y)].append(img[y,x])
        
        # Calcul des moyennes
        avg_colors = {k: np.mean(v, axis=0).astype(int) for k,v in color_samples.items()}
        
        # Mise à jour des références
        self.reference_data[mode_name] = {
            'zones': list(avg_colors.keys()),
            'couleurs': avg_colors,
            'seuil': 20  # Valeur par défaut
        }
        
        print(f"Calibration terminée pour {mode_name}")
        return avg_colors

if __name__ == "__main__":
    detector = ViewDetector(device_serial="EML-L09")  # Remplacer par votre serial USB
    
    # Mode detection
    input("Placez-vous dans un mode puis appuyez sur Entrée...")
    test_img = detector.capture_via_usb()
    detected = detector.detect_mode(test_img)
    print(f"\nMode détecté : {detected}")
    
    # Mode calibration (optionnel)
    if detected is None:
        new_mode = input("Nom du nouveau mode à calibrer : ")
        detector.calibrate_mode(new_mode)