import cv2
import numpy as np
import os

class UltimateViewDetector:
    def __init__(self):
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        
        # Configuration précise des zones (x1, y1, x2, y2)
        self.zones = {
            'city_logo': (74, 903, 243, 1060),
            'map_logo': (74, 903, 243, 1060),  # Même zone que city_logo
            'kingdom_logo': (2037, 944, 2174, 1064),
            'mail_logo': (1925, 971, 1983, 1028),  # Zone réduite
            'explore_marker': (128, 494, 128, 494)  # Point unique
        }
        
        # Couleurs BGR exactes avec tolérances
        self.colors = {
            'city_logo': {'expected': [9, 83, 132], 'tolerance': 15},
            'map_logo': {'expected': [20, 90, 140], 'tolerance': 15},
            'kingdom_logo': {'expected': [100, 200, 250], 'tolerance': 50},
            'mail_logo': {'expected': [150, 150, 150], 'tolerance': 30},
            'explore_marker': {'expected': [246, 36, 195], 'tolerance': 10}
        }

    def _check_zone_color(self, img, zone_name):
        """Vérifie la couleur moyenne d'une zone avec précision"""
        if zone_name not in self.zones or zone_name not in self.colors:
            return False
            
        x1, y1, x2, y2 = self.zones[zone_name]
        if y2 > img.shape[0] or x2 > img.shape[1]:
            return False
            
        roi = img[y1:y2, x1:x2]
        avg_color = np.mean(roi, axis=(0, 1))
        expected = self.colors[zone_name]['expected']
        tolerance = self.colors[zone_name]['tolerance']
        
        return np.all(np.abs(avg_color - expected) <= tolerance)

    def _check_point_color(self, img, point_name):
        """Vérifie la couleur d'un point spécifique"""
        if point_name not in self.zones or point_name not in self.colors:
            return False
            
        x, y, _, _ = self.zones[point_name]
        if y >= img.shape[0] or x >= img.shape[1]:
            return False
            
        pixel = img[y, x]
        expected = self.colors[point_name]['expected']
        tolerance = self.colors[point_name]['tolerance']
        
        return np.all(np.abs(pixel - expected) <= tolerance

    def detect_view(self, img):
        """Détection ultra-précise avec logique combinatoire"""
        if img is None:
            return 'unknown'
        
        # 1. Kingdom View doit avoir mail_logo ET city_logo
        has_mail_logo = self._check_zone_color(img, 'mail_logo')
        has_city_logo = self._check_zone_color(img, 'city_logo')
        has_kingdom_logo = self._check_zone_color(img, 'kingdom_logo')
        
        if has_mail_logo and has_city_logo and has_kingdom_logo:
            return 'kingdom_view'
            
        # 2. Explore View doit avoir city_logo ET explore_marker
        has_explore_marker = self._check_point_color(img, 'explore_marker')
        if has_city_logo and has_explore_marker:
            return 'explore_view'
            
        # 3. Différenciation City/Map par couleur précise
        if has_city_logo:
            # Analyse fine de la couleur du logo
            x, y = self.zones['city_logo'][0], self.zones['city_logo'][1]
            pixel = img[y, x]
            dist_city = np.linalg.norm(pixel - self.colors['city_logo']['expected'])
            dist_map = np.linalg.norm(pixel - self.colors['map_logo']['expected'])
            return 'city_view' if dist_city < dist_map else 'map_view'
            
        # 4. Map View par défaut si map_logo détecté
        if self._check_zone_color(img, 'map_logo'):
            return 'map_view'
            
        return 'unknown'

    def analyze_image(self, img_path):
        """Analyse complète avec rapport détaillé"""
        img = cv2.imread(img_path)
        if img is None:
            print(f"Erreur: Impossible de charger {img_path}")
            return
        
        view_type = self.detect_view(img)
        print(f"\nAnalyse de {os.path.basename(img_path)}")
        print(f"Vue détectée: {view_type}")
        
        # Vérification détaillée
        print("\nDétails des vérifications:")
        for zone in self.zones:
            if zone.endswith('_marker'):
                result = self._check_point_color(img, zone)
            else:
                result = self._check_zone_color(img, zone)
            print(f"- {zone}: {'OUI' if result else 'NON'}")
        
        # Affichage avec annotations
        display_img = img.copy()
        for zone_name in self.zones:
            x1, y1, x2, y2 = self.zones[zone_name]
            
            # Dessin différent pour les points et zones
            if x1 == x2 and y1 == y2:  # Point unique
                color = (0, 255, 255) if self._check_point_color(img, zone_name) else (0, 0, 255)
                cv2.circle(display_img, (x1, y1), 10, color, -1)
            else:  # Zone rectangulaire
                color = (0, 255, 0) if self._check_zone_color(img, zone_name) else (0, 0, 255)
                cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 2)
            
            # Texte d'identification
            cv2.putText(display_img, zone_name, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Affichage
        cv2.imshow('Résultats de détection', display_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = UltimateViewDetector()
    
    # Test sur toutes les vues
    test_images = [
        'city_view.png',
        'map_view.png',
        'explore_view.png',
        'kingdom_view.png'
    ]
    
    for img_file in test_images:
        img_path = os.path.join(detector.base_path, img_file)
        if os.path.exists(img_path):
            detector.analyze_image(img_path)