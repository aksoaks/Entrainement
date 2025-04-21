import os  
import cv2
import numpy as np

class FixedViewDetector:
    def __init__(self):
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        self.template_path = os.path.join(self.base_path, "templates/")
        
        # Configuration spécifique pour explore_marker
        self.explore_marker_config = {
            'template_path': os.path.join(self.template_path, "explore_marker.png"),
            'position': (128, 494),  # Point unique
            'color_range': {
                'min': [180, 25, 230],  # BGR minimum
                'max': [210, 45, 255]   # BGR maximum
            },
            'template_threshold': 0.85,
            'color_tolerance': 15
        }
        
        # Charger le template
        self.explore_template = cv2.imread(self.explore_marker_config['template_path'])
        if self.explore_template is None:
            print("Avertissement: Template explore_marker non chargé")

    def _detect_explore_marker(self, img):
        """Détection hybride du marqueur explore (template + couleur)"""
        x, y = self.explore_marker_config['position']
        
        # 1. Vérification couleur du pixel
        pixel = img[y, x]
        color_match = np.all(np.abs(pixel - self.explore_marker_config['color_range']['min']) <= self.explore_marker_config['color_tolerance'])
        
        # 2. Vérification par template matching autour du point
        if self.explore_template is not None:
            # Zone de recherche autour du point (50x50 pixels)
            margin = 25
            x1, y1 = max(0, x-margin), max(0, y-margin)
            x2, y2 = min(img.shape[1], x+margin), min(img.shape[0], y+margin)
            roi = img[y1:y2, x1:x2]
            
            if roi.size > 0 and roi.shape[0] >= self.explore_template.shape[0] and roi.shape[1] >= self.explore_template.shape[1]:
                res = cv2.matchTemplate(roi, self.explore_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                template_match = max_val > self.explore_marker_config['template_threshold']
            else:
                template_match = False
        else:
            template_match = False
        
        # Résultat final (les deux méthodes doivent concorder)
        return color_match and template_match

    def detect_view(self, img):
        """Détection avec la nouvelle méthode explore_marker"""
        if img is None:
            return 'unknown'
            
        # Détection explore_view en premier
        if self._detect_explore_marker(img):
            return 'explore_view'
            
        # ... (le reste de votre logique de détection)
        
        return 'unknown'

    def debug_explore_marker(self, img_path):
        """Fonction spéciale pour debugger explore_marker"""
        img = cv2.imread(img_path)
        if img is None:
            print("Erreur de chargement de l'image")
            return
            
        x, y = self.explore_marker_config['position']
        print(f"\nDebug explore_marker sur {os.path.basename(img_path)}:")
        
        # 1. Analyse couleur
        pixel = img[y, x]
        print(f"- Couleur du pixel: {pixel}")
        print(f"- Plage attendue: {self.explore_marker_config['color_range']['min']} à {self.explore_marker_config['color_range']['max']}")
        
        # 2. Analyse template
        if self.explore_template is not None:
            margin = 25
            x1, y1 = max(0, x-margin), max(0, y-margin)
            x2, y2 = min(img.shape[1], x+margin), min(img.shape[0], y+margin)
            roi = img[y1:y2, x1:x2]
            
            if roi.size > 0:
                res = cv2.matchTemplate(roi, self.explore_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                print(f"- Meilleure correspondance template: {max_val:.2f}")
                
                # Sauvegarde debug
                debug_img = roi.copy()
                cv2.circle(debug_img, (max_loc[0], max_loc[1]), 5, (0, 255, 0), 2)
                cv2.imwrite(os.path.join(self.base_path, "debug_results", "explore_debug.png"), debug_img)
                print(f"- Image debug sauvegardée")
            else:
                print("- ROI vide (hors limites)")
        else:
            print("- Template non chargé")
        
        # Résultat final
        detected = self._detect_explore_marker(img)
        print(f"\n>> explore_marker: {'DÉTECTÉ' if detected else 'NON DÉTECTÉ'}")

if __name__ == "__main__":
    detector = FixedViewDetector()
    
    # Test spécifique sur explore_view.png
    test_image = os.path.join(detector.base_path, "explore_view.png")
    if os.path.exists(test_image):
        detector.debug_explore_marker(test_image)
    else:
        print("Fichier explore_view.png introuvable")