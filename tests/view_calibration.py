import cv2
import numpy as np
import os

class EnhancedViewDetector:
    def __init__(self):
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        
        # Configuration précise des logos
        self.logo_config = {
            'city_logo': {
                'zone': (74, 903, 243, 1060),
                'color_sample': (150, 980),
                'expected_color': [9, 83, 132],  # BGR exact
                'tolerance': 15
            },
            'map_logo': {
                'zone': (74, 903, 243, 1060),  # Même zone mais couleur différente
                'color_sample': (150, 980),
                'expected_color': [20, 90, 140],  # BGR légèrement différent
                'tolerance': 15
            },
            'kingdom_logo': {
                'zone': (2037, 944, 2174, 1064),
                'color_sample': (2100, 1000),
                'expected_color': [100, 200, 250],
                'tolerance': 50
            },
            'mail_logo': {
                'zone': (1891, 948, 2027, 1053),
                'color_sample': (1950, 1000),
                'expected_color': [150, 150, 150],
                'tolerance': 30
            }
        }
        
        # Configuration des marqueurs spéciaux
        self.markers = {
            'explore_marker': {
                'position': (128, 494),
                'expected_color': [246, 36, 195],  # BGR
                'tolerance': 10
            }
        }

    def _check_logo(self, img, logo_name):
        """Vérifie la présence d'un logo spécifique"""
        config = self.logo_config.get(logo_name)
        if not config:
            return False
        
        x1, y1, x2, y2 = config['zone']
        if y2 > img.shape[0] or x2 > img.shape[1]:
            return False
            
        # Vérification couleur moyenne
        roi = img[y1:y2, x1:x2]
        avg_color = np.mean(roi, axis=(0, 1))
        return np.all(np.abs(avg_color - config['expected_color']) <= config['tolerance'])

    def _check_marker(self, img, marker_name):
        """Vérifie un marqueur ponctuel"""
        config = self.markers.get(marker_name)
        if not config:
            return False
            
        x, y = config['position']
        if y >= img.shape[0] or x >= img.shape[1]:
            return False
            
        return np.all(np.abs(img[y, x] - config['expected_color']) <= config['tolerance'])

    def detect_view(self, img):
        """Détection hiérarchique précise"""
        if img is None:
            return None
        
        # 1. Détection kingdom_view (logo royaume + logo mail)
        if (self._check_logo(img, 'kingdom_logo') and 
            self._check_logo(img, 'mail_logo')):
            return 'kingdom_view'
            
        # 2. Détection explore_view (logo ville + marqueur violet)
        if (self._check_logo(img, 'city_logo') and 
            self._check_marker(img, 'explore_marker')):
            return 'explore_view'
            
        # 3. Différenciation city_view/map_view
        if self._check_logo(img, 'city_logo'):
            # Vérification fine de la couleur pour différencier
            x, y = self.logo_config['city_logo']['color_sample']
            pixel = img[y, x]
            city_color = self.logo_config['city_logo']['expected_color']
            map_color = self.logo_config['map_logo']['expected_color']
            
            # Distance aux couleurs attendues
            dist_city = np.linalg.norm(pixel - city_color)
            dist_map = np.linalg.norm(pixel - map_color)
            
            return 'city_view' if dist_city < dist_map else 'map_view'
            
        # 4. Détection map_view par défaut si logo map trouvé
        if self._check_logo(img, 'map_logo'):
            return 'map_view'
            
        return 'unknown'

    def analyze_view(self, img_path):
        """Analyse complète avec affichage"""
        img = cv2.imread(img_path)
        if img is None:
            print(f"Erreur: Impossible de charger {img_path}")
            return
        
        view_type = self.detect_view(img)
        print(f"\nAnalyse de {os.path.basename(img_path)}")
        print(f"Vue détectée: {view_type}")
        
        # Affichage des résultats de vérification
        print("\nDétails de détection:")
        for logo in self.logo_config:
            print(f"- {logo}: {'OUI' if self._check_logo(img, logo) else 'NON'}")
        for marker in self.markers:
            print(f"- {marker}: {'OUI' if self._check_marker(img, marker) else 'NON'}")
        
        # Création de l'image annotée
        display_img = img.copy()
        
        # Annotation des zones vérifiées
        for logo, config in self.logo_config.items():
            x1, y1, x2, y2 = config['zone']
            if y2 <= img.shape[0] and x2 <= img.shape[1]:
                color = (0, 255, 0) if self._check_logo(img, logo) else (0, 0, 255)
                cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display_img, logo, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Annotation des marqueurs
        for marker, config in self.markers.items():
            x, y = config['position']
            if y < img.shape[0] and x < img.shape[1]:
                color = (255, 0, 255) if self._check_marker(img, marker) else (0, 165, 255)
                cv2.circle(display_img, (x, y), 10, color, -1)
                cv2.putText(display_img, marker, (x-50, y-15), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Affichage
        cv2.imshow('Detection Results', display_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = EnhancedViewDetector()
    
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
            detector.analyze_view(img_path)