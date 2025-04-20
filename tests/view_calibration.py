import cv2
import numpy as np
import os

class PrecisionViewDetector:
    def __init__(self):
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        self.template_path = os.path.join(self.base_path, "templates/")
        
        # Zones de recherche spécifiques
        self.search_zones = {
            'explore_area': (375, 57, 2182, 921)  # x1, y1, x2, y2
        }
        
        # Chargement des templates critiques seulement
        self.templates = {
            'barbarian': self._load_template('barbarian.png'),
            'food': self._load_template('food.png'),
            'gems': self._load_template('gems.png'),
            'gold': self._load_template('gold.png'),
            'stone': self._load_template('stone.png'),
            'wood': self._load_template('wood.png')
        }
        
        # Configuration précise des vues
        self.view_profiles = {
            'city_view': {
                'logo_zone': (74, 903, 243, 1060),
                'color_sample': (150, 980),
                'expected_color': [9, 83, 132],  # BGR exact
                'tolerance': 15
            },
            'map_view': {
                'logo_zone': (74, 903, 243, 1060),
                'color_sample': (150, 980),
                'expected_color': [9, 83, 132],
                'tolerance': 15
            },
            'explore_view': {
                'special_marker': (125, 501, [197, 34, 251], 10),  # x, y, BGR, tol
                'search_zone': 'explore_area'
            },
            'kingdom_view': {
                'logo_zone': (2037, 944, 2174, 1064),
                'color_sample': (2100, 1000),
                'expected_color': [100, 200, 250],
                'tolerance': 50
            }
        }

    def _load_template(self, filename):
        """Charge un template avec gestion d'erreur"""
        path = os.path.join(self.template_path, filename)
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise FileNotFoundError(f"Template manquant: {filename}")
        if img.shape[2] == 4:
            return (img[:,:,:3], img[:,:,3])  # Image + alpha
        return (img, None)  # Image seulement

    def _crop_search_zone(self, img, zone_name):
        """Découpe la zone de recherche spécifique"""
        if zone_name not in self.search_zones:
            return img
        x1, y1, x2, y2 = self.search_zones[zone_name]
        return img[y1:y2, x1:x2]

    def detect_view(self, img):
        """Détection précise de la vue active"""
        if img is None:
            return None
        
        # 1. Détection prioritaire de kingdom_view
        k_config = self.view_profiles['kingdom_view']
        k_zone = k_config['logo_zone']
        if all(coord < img.shape[1] if i%2 == 0 else coord < img.shape[0] for i, coord in enumerate(k_zone)):
            k_roi = img[k_zone[1]:k_zone[3], k_zone[0]:k_zone[2]]
            avg_color = np.mean(k_roi, axis=(0, 1))
            if np.all(np.abs(avg_color - k_config['expected_color']) <= k_config['tolerance']):
                return 'kingdom_view'

        # 2. Détection explore_view (marqueur violet strict)
        ex_config = self.view_profiles['explore_view']
        ex_x, ex_y, ex_color, ex_tol = ex_config['special_marker']
        if ex_y < img.shape[0] and ex_x < img.shape[1]:
            if np.all(np.abs(img[ex_y, ex_x] - ex_color) <= ex_tol):
                return 'explore_view'

        # 3. Différenciation city_view/map_view
        c_config = self.view_profiles['city_view']
        c_x, c_y = c_config['color_sample']
        if c_y < img.shape[0] and c_x < img.shape[1]:
            if np.all(np.abs(img[c_y, c_x] - c_config['expected_color']) <= c_config['tolerance']):
                return 'city_view'
        
        return 'map_view'

    def detect_explore_features(self, img):
        """Détection spécifique à explore_view seulement"""
        if self.detect_view(img) != 'explore_view':
            return None
        
        results = {
            'barbarians': [],
            'resources': []
        }
        
        # Recherche dans la zone spécifique
        zone_name = self.view_profiles['explore_view']['search_zone']
        search_img = self._crop_search_zone(img, zone_name)
        if search_img is None:
            return results
        
        # Détection des barbares
        barb_template, barb_alpha = self.templates['barbarian']
        res = cv2.matchTemplate(search_img, barb_template, cv2.TM_CCOEFF_NORMED, mask=barb_alpha)
        loc = np.where(res >= 0.85)  # Seuil élevé pour précision
        for pt in zip(*loc[::-1]):
            results['barbarians'].append({
                'position': (pt[0] + self.search_zones[zone_name][0], 
                            pt[1] + self.search_zones[zone_name][1])
            })

        # Détection des ressources
        for res_name in ['food', 'gems', 'gold', 'stone', 'wood']:
            template, alpha = self.templates[res_name]
            res = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED, mask=alpha)
            loc = np.where(res >= 0.8)
            for pt in zip(*loc[::-1]):
                results['resources'].append({
                    'type': res_name,
                    'position': (pt[0] + self.search_zones[zone_name][0], 
                                pt[1] + self.search_zones[zone_name][1])
                })
        
        return results

    def analyze_and_display(self, img_path):
        """Analyse complète avec affichage OpenCV"""
        img = cv2.imread(img_path)
        if img is None:
            print(f"Erreur: Impossible de charger {img_path}")
            return
        
        view_type = self.detect_view(img)
        print(f"\nVue détectée: {view_type}")
        
        # Création de l'image de résultat
        display_img = img.copy()
        
        # Annotation selon la vue
        if view_type in self.view_profiles:
            config = self.view_profiles[view_type]
            
            # Zone logo
            if 'logo_zone' in config:
                x1, y1, x2, y2 = config['logo_zone']
                cv2.rectangle(display_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display_img, f"{view_type} logo", (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Marqueur spécial
            if view_type == 'explore_view' and 'special_marker' in config:
                x, y, _, _ = config['special_marker']
                cv2.circle(display_img, (x, y), 10, (255, 0, 255), -1)
                cv2.putText(display_img, "Marqueur violet", (x-50, y-15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
        
        # Détection des features si explore_view
        features = None
        if view_type == 'explore_view':
            features = self.detect_explore_features(img)
            
            # Zone de recherche
            x1, y1, x2, y2 = self.search_zones['explore_area']
            cv2.rectangle(display_img, (x1, y1), (x2, y2), (255, 255, 0), 2)
            
            # Barbares
            if features and features['barbarians']:
                for barb in features['barbarians']:
                    x, y = barb['position']
                    cv2.circle(display_img, (x, y), 8, (0, 0, 255), -1)
                    cv2.putText(display_img, "Barbare", (x+10, y), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Ressources
            if features and features['resources']:
                for res in features['resources']:
                    x, y = res['position']
                    color = {
                        'food': (0, 255, 255),
                        'gems': (255, 0, 255),
                        'gold': (0, 215, 255),
                        'stone': (130, 130, 130),
                        'wood': (0, 165, 255)
                    }.get(res['type'], (255, 255, 255))
                    cv2.circle(display_img, (x, y), 6, color, -1)
                    cv2.putText(display_img, res['type'], (x+10, y), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Affichage des résultats
        cv2.imshow('Resultats Detection', display_img)
        print("Appuyez sur une touche pour continuer...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Affichage console
        if view_type == 'explore_view' and features:
            print("\nDétails exploration:")
            print(f"Barbares trouvés: {len(features['barbarians'])}")
            print("Ressources trouvées:")
            for res in features['resources']:
                print(f"- {res['type']} à {res['position']}")

if __name__ == "__main__":
    detector = PrecisionViewDetector()
    
    # Test sur toutes les vues
    for view in ['city_view', 'map_view', 'explore_view', 'kingdom_view']:
        img_path = os.path.join(detector.base_path, f"{view}.png")
        if os.path.exists(img_path):
            print(f"\nAnalyse de {view}...")
            detector.analyze_and_display(img_path)