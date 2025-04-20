import cv2
import numpy as np
import os
from matplotlib import pyplot as plt

class ViewAnalyzer:
    def __init__(self):
        # Configuration basée sur vos captures
        self.view_profiles = {
            'city_view': {
                'logo_zone': (74, 903, 243, 1060),
                'color_check': (150, 980, [200, 150, 50], 40)  # x, y, BGR, tolérance
            },
            'map_view': {
                'logo_zone': (74, 903, 243, 1060),
                'color_check': (150, 980, [200, 150, 50], 40),
                'diff_check': None
            },
            'explore_view': {
                'logo_zone': (74, 903, 243, 1060),
                'color_check': (150, 980, [200, 150, 50], 40),
                'special_marker': (125, 501, [197, 34, 251], 10)  # x, y, BGR, tolérance
            },
            'kingdom_view': {
                'logo_zone': (2037, 944, 2174, 1064),
                'color_check': (2100, 1000, [250, 200, 100], 50)
            }
        }
        
        # Chemin vers vos captures
        self.sample_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        self.samples = {
            'city_view': 'city_view.png',
            'explore_view': 'explore_view.png',
            'kingdom_view': 'kingdom_view.png',
            'map_view': 'map_view.png'
        }

    def load_image(self, view_name):
        """Charge une image de référence"""
        path = os.path.join(self.sample_path, self.samples[view_name])
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"Image non trouvée: {path}")
        return img

    def analyze_all_views(self):
        """Analyse toutes les vues et génère un rapport"""
        plt.figure(figsize=(15, 10))
        
        for i, (view_name, _) in enumerate(self.samples.items(), 1):
            img = self.load_image(view_name)
            logo = self.extract_logo(img, view_name)
            
            # Affichage
            plt.subplot(2, 4, i)
            plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            plt.title(f"Original: {view_name}")
            
            plt.subplot(2, 4, i+4)
            if logo is not None:
                plt.imshow(cv2.cvtColor(logo, cv2.COLOR_BGR2RGB))
            plt.title(f"Logo extrait")
        
        plt.tight_layout()
        plt.show()

    def extract_logo(self, img, view_name):
        """Extrait la zone du logo caractéristique"""
        config = self.view_profiles.get(view_name)
        if not config or 'logo_zone' not in config:
            return None
            
        x1, y1, x2, y2 = config['logo_zone']
        return img[y1:y2, x1:x2]

    def verify_view(self, view_name):
        """Vérifie la détection sur une vue spécifique"""
        img = self.load_image(view_name)
        config = self.view_profiles[view_name]
        
        print(f"\n=== Analyse de {view_name} ===")
        
        # Vérification du logo principal
        logo = self.extract_logo(img, view_name)
        if logo is None:
            print("Erreur: Zone logo non trouvée")
            return
            
        # Vérification couleur
        x, y, expected_color, tolerance = config['color_check']
        actual_color = img[y, x]
        color_match = np.all(np.abs(actual_color - expected_color) <= tolerance)
        
        print(f"Couleur logo: {actual_color} (attendu: {expected_color})")
        print(f"Match couleur: {'OK' if color_match else 'FAIL'}")
        
        # Vérification spéciale pour explore_view
        if view_name == 'explore_view':
            x, y, expected_color, tolerance = config['special_marker']
            actual_color = img[y, x]
            special_match = np.all(np.abs(actual_color - expected_color) <= tolerance)
            
            print(f"Marqueur spécial: {actual_color} (attendu: {expected_color})")
            print(f"Match marqueur: {'OK' if special_match else 'FAIL'}")
        
        # Affichage
        plt.figure(figsize=(12, 5))
        plt.subplot(121)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(f"Vue complète: {view_name}")
        
        plt.subplot(122)
        plt.imshow(cv2.cvtColor(logo, cv2.COLOR_BGR2RGB))
        plt.title("Zone logo analysée")
        plt.show()

    def detect_view(self, img_path):
        """Détecte le type de vue d'une image donnée"""
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"Image non trouvée: {img_path}")
        
        # Détection prioritaire de kingdom_view
        kingdom_config = self.view_profiles['kingdom_view']
        k_x1, k_y1, k_x2, k_y2 = kingdom_config['logo_zone']
        kingdom_roi = img[k_y1:k_y2, k_x1:k_x2]
        k_color_check = kingdom_config['color_check']
        
        if self._check_color_match(img[k_color_check[1], k_color_check[0]], 
                                 k_color_check[2], k_color_check[3]):
            return 'kingdom_view'
        
        # Check explore_view (marqueur violet)
        explore_config = self.view_profiles['explore_view']
        ex_check = explore_config['special_marker']
        if (ex_check[1] < img.shape[0] and ex_check[0] < img.shape[1] and
            self._check_color_match(img[ex_check[1], ex_check[0]], 
                                  ex_check[2], ex_check[3])):
            return 'explore_view'
            
        # Différenciation city_view/map_view
        city_config = self.view_profiles['city_view']
        c_color_check = city_config['color_check']
        if self._check_color_match(img[c_color_check[1], c_color_check[0]], 
                                 c_color_check[2], c_color_check[3]):
            return 'city_view'
        else:
            return 'map_view'

    def _check_color_match(self, color, expected, tolerance):
        return np.all(np.abs(color - expected) <= tolerance)

if __name__ == "__main__":
    analyzer = ViewAnalyzer()
    
    # 1. Analyse complète des échantillons
    print("Analyse des captures de référence...")
    analyzer.analyze_all_views()
    
    # 2. Détection sur une image spécifique
    test_image = "D:/Users/Documents/Code/Python/Entrainement/tests/map_view.png"
    detected_view = analyzer.detect_view(test_image)
    print(f"\nDétection sur '{os.path.basename(test_image)}': {detected_view}")
    
    # 3. Vérification détaillée par vue
    analyzer.verify_view('explore_view')