import cv2
import numpy as np
import os
from datetime import datetime

class DebugViewDetector:
    def __init__(self):
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        
        # Configuration avec logging activé
        self.features = {
            'city_logo': {
                'zone': (70, 900, 250, 1070),
                'color_range': {
                    'min': [120, 70, 0],
                    'max': [140, 100, 20]
                },
                'debug_color': (0, 255, 0)  # Vert pour visualisation
            },
            'explore_marker': {
                'zone': (120, 490, 135, 505),
                'color_range': {
                    'min': [180, 25, 230],
                    'max': [210, 45, 255]
                },
                'debug_color': (255, 0, 255)  # Magenta
            },
            'kingdom_logo': {
                'zone': (2030, 940, 2180, 1070),
                'color_range': {
                    'min': [90, 180, 240],
                    'max': [110, 220, 260]
                },
                'debug_color': (0, 255, 255)  # Jaune
            }
        }

    def _check_feature(self, img, feature_name):
        """Vérifie une feature avec logging"""
        feat = self.features.get(feature_name)
        if not feat:
            print(f"Feature {feature_name} non configurée")
            return False
            
        x1, y1, x2, y2 = feat['zone']
        roi = img[y1:y2, x1:x2]
        
        if roi.size == 0:
            print(f"Zone {feature_name} hors limites")
            return False
            
        avg_color = np.mean(roi, axis=(0, 1))
        min_val = np.array(feat['color_range']['min'])
        max_val = np.array(feat['color_range']['max'])
        
        print(f"\nAnalyse {feature_name}:")
        print(f"- Position: ({x1},{y1}) à ({x2},{y2})")
        print(f"- Couleur moyenne: {avg_color}")
        print(f"- Plage attendue: {min_val} à {max_val}")
        
        result = np.all(avg_color >= min_val) and np.all(avg_color <= max_val)
        print(f"- Résultat: {'OK' if result else 'NON'}")
        
        return result

    def detect_view(self, img):
        """Détection avec logging complet"""
        print("\n" + "="*50)
        print("Début de l'analyse d'image")
        print("="*50)
        
        if img is None:
            print("ERREUR: Image non chargée")
            return 'error'
        
        # Détection hiérarchique
        print("\n[1/3] Vérification explore_marker...")
        if self._check_feature(img, 'explore_marker'):
            print(">> Détection: EXPLORE_VIEW")
            return 'explore_view'
            
        print("\n[2/3] Vérification kingdom_logo...")
        if self._check_feature(img, 'kingdom_logo'):
            print(">> Détection: KINGDOM_VIEW")
            return 'kingdom_view'
            
        print("\n[3/3] Vérification city_logo...")
        city_score = self._get_zone_similarity(img, 'city_logo')
        print(f"- Similarité city_logo: {city_score:.2f}/1.0")
        
        if city_score > 0.7:
            print(">> Détection: CITY_VIEW")
            return 'city_view'
            
        print(">> Aucune vue reconnue")
        return 'unknown'

    def _get_zone_similarity(self, img, feature_name):
        """Calcule un score de similarité avec logging"""
        feat = self.features.get(feature_name)
        if not feat:
            return 0
            
        x1, y1, x2, y2 = feat['zone']
        roi = img[y1:y2, x1:x2]
        
        if roi.size == 0:
            return 0
            
        avg_color = np.mean(roi, axis=(0, 1))
        target = (np.array(feat['color_range']['min']) + np.array(feat['color_range']['max'])) / 2
        distance = np.linalg.norm(avg_color - target)
        max_distance = np.linalg.norm([255, 255, 255])
        similarity = 1 - (distance / max_distance)
        
        print(f"Similarité {feature_name}:")
        print(f"- Couleur actuelle: {avg_color}")
        print(f"- Couleur cible: {target}")
        print(f"- Score: {similarity:.2f}")
        
        return similarity

    def process_image(self, img_path):
        """Traite une image avec sauvegarde des résultats"""
        print(f"\n\n{'#'*20} Traitement de {os.path.basename(img_path)} {'#'*20}")
        
        img = cv2.imread(img_path)
        if img is None:
            print(f"ERREUR: Impossible de charger {img_path}")
            return
            
        # Détection et logging
        view_type = self.detect_view(img)
        
        # Sauvegarde du résultat
        output_dir = os.path.join(self.base_path, "debug_results")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"debug_{timestamp}_{os.path.basename(img_path)}")
        
        cv2.imwrite(output_path, img)
        print(f"\nRésultats sauvegardés dans: {output_path}")
        print(f"Conclusion: Vue détectée = {view_type.upper()}")
        
        return view_type

if __name__ == "__main__":
    detector = DebugViewDetector()
    
    # Liste des images à analyser
    test_images = [
        'city_view.png',
        'map_view.png',
        'explore_view.png',
        'kingdom_view.png'
    ]
    
    # Traitement de chaque image
    for img_file in test_images:
        img_path = os.path.join(detector.base_path, img_file)
        if os.path.exists(img_path):
            detector.process_image(img_path)
        else:
            print(f"Fichier introuvable: {img_path}")
    
    print("\nTraitement terminé. Vérifiez les logs ci-dessus.")