import cv2
import numpy as np
import os

class FinalViewDetector:
    def __init__(self):
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        
        # Configuration des zones de détection (x1, y1, x2, y2)
        self.detection_zones = {
            'city_logo': (74, 903, 243, 1060),
            'map_logo': (74, 903, 243, 1060),  # Même zone que city_logo
            'kingdom_logo': (2037, 944, 2174, 1064),
            'mail_icon': (1925, 971, 1983, 1028),  # Zone réduite
            'explore_marker': (128, 494, 128, 494)  # Point unique
        }
        
        # Couleurs BGR attendues avec tolérances
        self.expected_colors = {
            'city_logo': {'bgr': [132, 83, 9], 'tolerance': 15},
            'map_logo': {'bgr': [140, 90, 20], 'tolerance': 15},
            'kingdom_logo': {'bgr': [250, 200, 100], 'tolerance': 50},
            'mail_icon': {'bgr': [150, 150, 150], 'tolerance': 30},
            'explore_marker': {'bgr': [195, 36, 246], 'tolerance': 10}
        }

    def _check_zone_color(self, img, zone_name):
        """Vérifie si une zone correspond à la couleur attendue"""
        if zone_name not in self.detection_zones or zone_name not in self.expected_colors:
            return False
            
        x1, y1, x2, y2 = self.detection_zones[zone_name]
        if y2 > img.shape[0] or x2 > img.shape[1]:
            return False
            
        roi = img[y1:y2, x1:x2]
        avg_color = np.mean(roi, axis=(0, 1))
        expected = self.expected_colors[zone_name]['bgr']
        tolerance = self.expected_colors[zone_name]['tolerance']
        
        return np.all(np.abs(avg_color - expected) <= tolerance)

    def _check_point_color(self, img, point_name):
        """Vérifie la couleur d'un point spécifique"""
        if point_name not in self.detection_zones or point_name not in self.expected_colors:
            return False
            
        x, y, _, _ = self.detection_zones[point_name]
        if y >= img.shape[0] or x >= img.shape[1]:
            return False
            
        pixel = img[y, x]
        expected = self.expected_colors[point_name]['bgr']
        tolerance = self.expected_colors[point_name]['tolerance']
        
        return np.all(np.abs(pixel - expected) <= tolerance)

    def detect_current_view(self, img):
        """Détection précise de la vue actuelle"""
        if img is None:
            return 'unknown'
        
        # Détection kingdom_view (mail_icon + kingdom_logo)
        if (self._check_zone_color(img, 'mail_icon') and 
            self._check_zone_color(img, 'kingdom_logo')):
            return 'kingdom_view'
            
        # Détection explore_view (city_logo + explore_marker)
        if (self._check_zone_color(img, 'city_logo') and 
            self._check_point_color(img, 'explore_marker')):
            return 'explore_view'
            
        # Différenciation city_view/map_view
        if self._check_zone_color(img, 'city_logo'):
            # Analyse fine de la couleur
            x, y = self.detection_zones['city_logo'][0], self.detection_zones['city_logo'][1]
            pixel = img[y, x]
            dist_city = np.linalg.norm(pixel - self.expected_colors['city_logo']['bgr'])
            dist_map = np.linalg.norm(pixel - self.expected_colors['map_logo']['bgr'])
            return 'city_view' if dist_city < dist_map else 'map_view'
            
        # Détection map_view par défaut
        if self._check_zone_color(img, 'map_logo'):
            return 'map_view'
            
        return 'unknown'

    def analyze_view(self, img_path):
        """Analyse complète avec visualisation"""
        img = cv2.imread(img_path)
        if img is None:
            print(f"Erreur: Impossible de charger {img_path}")
            return
        
        view_type = self.detect_current_view(img)
        print(f"\nAnalyse de {os.path.basename(img_path)}")
        print(f"Vue détectée: {view_type}")
        
        # Vérification détaillée
        print("\nDétails des détections:")
        for zone in self.detection_zones:
            if zone.endswith('_marker'):
                result = self._check_point_color(img, zone)
            else:
                result = self._check_zone_color(img, zone)
            print(f"- {zone}: {'DÉTECTÉ' if result else 'NON DÉTECTÉ'}")
        
        # Affichage avec annotations
        display_img = img.copy()
        for zone_name, (x1, y1, x2, y2) in self.detection_zones.items():
            # Déterminer la couleur d'affichage
            if zone_name.endswith('_marker'):
                detected = self._check_point_color(img, zone_name)
            else:
                detected = self._check_zone_color(img, zone_name)
                
            color = (0, 255, 0) if detected else (0, 0, 255)  # Vert ou rouge
            
            # Dessiner la zone
            if x1 == x2 and y1 == y2:  # Point unique
                cv2.circle(display_img, (x1, y1), 10, color, -1)
            else:  # Zone rectangulaire
                cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 2)
            
            # Ajouter le nom de la zone
            cv2.putText(display_img, zone_name, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Afficher le résultat
        cv2.imshow('Résultat de la détection', display_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = FinalViewDetector()
    
    # Liste des images à analyser
    test_images = [
        'city_view.png',
        'map_view.png',
        'explore_view.png',
        'kingdom_view.png'
    ]
    
    # Analyse de chaque image
    for img_file in test_images:
        img_path = os.path.join(detector.base_path, img_file)
        if os.path.exists(img_path):
            detector.analyze_view(img_path)