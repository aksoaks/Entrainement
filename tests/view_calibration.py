import cv2
import numpy as np
import os
from datetime import datetime

class TemplateViewDetector:
    def __init__(self):
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        self.template_path = os.path.join(self.base_path, "templates/")
        
        # Configuration des zones de détection
        self.detection_zones = {
            'goto_city': (122, 946, 201, 1014),    # Depuis map_view/explore_view/kingdom_view
            'goto_map': (123, 943, 199, 1017),     # Depuis city_view
            'explore_marker': (128, 494, 128, 494), # Point unique
            'mail_button': (1926, 975, 1986, 1027) # kingdom_view seulement
        }
        
        # Seuils de correspondance
        self.template_thresholds = {
            'goto_city': 0.85,
            'goto_map': 0.85,
            'explore_marker': 0.9,
            'mail_button': 0.8
        }
        
        # Chargement des templates
        self.templates = self._load_templates()

    def _load_templates(self):
        """Charge les templates depuis le dossier"""
        templates = {}
        for feature in ['goto_city', 'goto_map', 'explore_marker', 'mail_button']:
            path = os.path.join(self.template_path, f"{feature}.png")
            if os.path.exists(path):
                template = cv2.imread(path, cv2.IMREAD_COLOR)
                if template is not None:
                    templates[feature] = template
                    print(f"Template chargé: {feature} ({template.shape[1]}x{template.shape[0]})")
                else:
                    print(f"Erreur: Impossible de charger {path}")
            else:
                print(f"Avertissement: Template manquant {path}")
        return templates

    def _match_template(self, img, feature_name):
        """Fait une correspondance de template dans la zone spécifique"""
        if feature_name not in self.templates or feature_name not in self.detection_zones:
            return False
            
        template = self.templates[feature_name]
        x1, y1, x2, y2 = self.detection_zones[feature_name]
        
        # Découpage de la zone d'intérêt
        roi = img[y1:y2, x1:x2]
        if roi.size == 0:
            return False
            
        # Correspondance de template
        res = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        
        return max_val > self.template_thresholds[feature_name]

    def detect_view(self, img):
        """Détection basée sur les templates et zones spécifiques"""
        if img is None:
            return 'unknown'
        
        # Détection hiérarchique
        if self._match_template(img, 'mail_button') and self._match_template(img, 'goto_city'):
            return 'kingdom_view'
            
        if self._match_template(img, 'explore_marker'):
            if self._match_template(img, 'goto_city'):
                return 'explore_view'
            return 'unknown'
            
        if self._match_template(img, 'goto_map'):
            return 'city_view'
            
        if self._match_template(img, 'goto_city'):
            return 'map_view'
            
        return 'unknown'

    def analyze_test_images(self):
        """Analyse les images de test avec rapports détaillés"""
        test_images = [f"image_test{i}.png" for i in range(1, 5)]
        
        for img_file in test_images:
            img_path = os.path.join(self.base_path, img_file)
            if not os.path.exists(img_path):
                print(f"\nImage manquante: {img_file}")
                continue
                
            img = cv2.imread(img_path)
            if img is None:
                print(f"\nErreur de chargement: {img_file}")
                continue
                
            print(f"\n{'#'*40}")
            print(f"Analyse de {img_file}")
            print(f"{'#'*40}")
            
            # Détection complète
            view = self.detect_view(img)
            print(f"\n>> Vue détectée: {view.upper()}")
            
            # Rapport détaillé
            print("\nDétails des détections:")
            for feature in self.detection_zones:
                matched = self._match_template(img, feature)
                print(f"- {feature}: {'DÉTECTÉ' if matched else 'NON DÉTECTÉ'}")
                
                # Sauvegarde debug
                self._save_debug(img, feature, matched)
            
            print(f"\n{'#'*40}")

    def _save_debug(self, img, feature, matched):
        """Sauvegarde les images de debug"""
        debug_dir = os.path.join(self.base_path, "debug_results")
        os.makedirs(debug_dir, exist_ok=True)
        
        x1, y1, x2, y2 = self.detection_zones[feature]
        roi = img[y1:y2, x1:x2]
        
        if roi.size > 0:
            status = "detected" if matched else "missed"
            timestamp = datetime.now().strftime("%H%M%S")
            cv2.imwrite(
                os.path.join(debug_dir, f"debug_{feature}_{status}_{timestamp}.png"),
                roi
            )

if __name__ == "__main__":
    detector = TemplateViewDetector()
    
    # 1. Vérification des templates chargés
    print("\nTemplates chargés:")
    for name, template in detector.templates.items():
        print(f"- {name}: {template.shape[1]}x{template.shape[0]}")
    
    # 2. Analyse des images de test
    print("\nDébut de l'analyse des images...")
    detector.analyze_test_images()