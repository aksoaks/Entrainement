import cv2
import numpy as np
import os
from matplotlib import pyplot as plt

class AdvancedViewDetector:
    def __init__(self):
        # Chemins des images
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        self.template_path = os.path.join(self.base_path, "templates/")
        
        # Chargement des templates
        self.templates = {
            'barbarian': self._load_template('barbarian.png'),
            'food': self._load_template('food.png'),
            'gems': self._load_template('gems.png'),
            'gold': self._load_template('gold.png'),
            'stone': self._load_template('stone.png'),
            'wood': self._load_template('wood.png')
        }
        
        # Configuration des vues
        self.view_config = {
            'city_view': {
                'logo_zone': (74, 903, 243, 1060),
                'expected_color': [9, 83, 132],  # BGR du screenshot
                'tolerance': 15
            },
            'map_view': {
                'logo_zone': (74, 903, 243, 1060),
                'expected_color': [9, 83, 132],
                'tolerance': 15
            },
            'explore_view': {
                'logo_zone': (74, 903, 243, 1060),
                'expected_color': [9, 83, 132],
                'tolerance': 15,
                'special_marker': {
                    'position': (125, 501),
                    'color': [197, 34, 251],  # BGR violet
                    'tolerance': 10
                },
                'required_templates': ['barbarian']  # Templates requis
            },
            'kingdom_view': {
                'logo_zone': (2037, 944, 2174, 1064),
                'expected_color': [100, 200, 250],
                'tolerance': 50,
                'required_templates': []  # Aucun template requis
            }
        }

    def _load_template(self, filename):
        """Charge un template avec gestion de la transparence"""
        path = os.path.join(self.template_path, filename)
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        
        if img is None:
            raise FileNotFoundError(f"Template non trouvé: {path}")
            
        # Séparation des canaux couleur et alpha
        if img.shape[2] == 4:  # Avec canal alpha
            template = img[:,:,:3]
            alpha = img[:,:,3]
            return (template, alpha)
        else:
            return (img, None)

    def _match_template(self, img, template_data):
        """Fait une correspondance de template avec gestion de la transparence"""
        template, alpha = template_data
        method = cv2.TM_CCOEFF_NORMED
        
        if alpha is not None:
            # Crée un masque à partir du canal alpha
            mask = cv2.merge([alpha, alpha, alpha])
            res = cv2.matchTemplate(img, template, method, mask=mask)
        else:
            res = cv2.matchTemplate(img, template, method)
            
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val  # Retourne le score de correspondance

    def detect_resources(self, img):
        """Détecte toutes les ressources présentes"""
        found_resources = []
        for res_name, template in self.templates.items():
            if res_name == 'barbarian':
                continue  # Géré séparément
                
            score = self._match_template(img, template)
            if score > 0.8:  # Seuil de détection
                found_resources.append(res_name)
        return found_resources

    def detect_view(self, img_path):
        """Détection de la vue avec templates"""
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"Image non trouvée: {img_path}")
        
        # 1. Détection kingdom_view (logo unique)
        kingdom_config = self.view_config['kingdom_view']
        k_roi = self._get_roi(img, kingdom_config['logo_zone'])
        if k_roi is not None:
            avg_color = np.mean(k_roi, axis=(0, 1))
            if self._color_in_range(avg_color, kingdom_config['expected_color'], kingdom_config['tolerance']):
                return 'kingdom_view'

        # 2. Détection explore_view (marqueur violet + barbares)
        explore_config = self.view_config['explore_view']
        ex_pos = explore_config['special_marker']['position']
        if (ex_pos[1] < img.shape[0] and ex_pos[0] < img.shape[1]):
            pixel = img[ex_pos[1], ex_pos[0]]
            if self._color_in_range(pixel, 
                                  explore_config['special_marker']['color'], 
                                  explore_config['special_marker']['tolerance']):
                # Vérification des barbares par template matching
                barb_score = self._match_template(img, self.templates['barbarian'])
                if barb_score > 0.8:
                    return 'explore_view'

        # 3. Détection city_view/map_view
        city_config = self.view_config['city_view']
        c_roi = self._get_roi(img, city_config['logo_zone'])
        if c_roi is not None:
            avg_color = np.mean(c_roi, axis=(0, 1))
            if self._color_in_range(avg_color, city_config['expected_color'], city_config['tolerance']):
                return 'city_view'
                
        return 'map_view'

    def _get_roi(self, img, zone):
        """Extrait une région d'intérêt avec vérification des limites"""
        x1, y1, x2, y2 = zone
        if y2 <= img.shape[0] and x2 <= img.shape[1]:
            return img[y1:y2, x1:x2]
        return None

    def _color_in_range(self, color, expected, tolerance):
        return np.all(np.abs(color - expected) <= tolerance)

    def analyze_screen(self, img_path):
        """Analyse complète avec visualisation"""
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"Image non trouvée: {img_path}")
        
        # Détection
        view_type = self.detect_view(img_path)
        resources = self.detect_resources(img)
        
        # Visualisation
        plt.figure(figsize=(15, 8))
        
        # Image originale
        plt.subplot(231)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(f"Vue: {view_type}")
        
        # Zones caractéristiques
        zones = {
            'Logo bas gauche': self.view_config[view_type]['logo_zone'],
            'Ressources': "Détection automatique"
        }
        
        if view_type == 'explore_view':
            zones['Marqueur violet'] = self.view_config['explore_view']['special_marker']['position']
        
        # Dessin des zones
        img_marked = img.copy()
        for zone_name, zone in zones.items():
            if isinstance(zone, tuple) and len(zone) == 4:
                x1, y1, x2, y2 = zone
                cv2.rectangle(img_marked, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img_marked, zone_name, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            elif isinstance(zone, tuple) and len(zone) == 2:
                x, y = zone
                cv2.circle(img_marked, (x, y), 10, (255, 0, 255), -1)
                cv2.putText(img_marked, zone_name, (x-50, y-15), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
        
        plt.subplot(232)
        plt.imshow(cv2.cvtColor(img_marked, cv2.COLOR_BGR2RGB))
        plt.title("Zones caractéristiques")
        
        # Détection des ressources
        plt.subplot(233)
        if resources:
            res_text = "\n".join(resources)
            plt.text(0.5, 0.5, res_text, ha='center', va='center', fontsize=12)
            plt.title("Ressources détectées")
        else:
            plt.title("Aucune ressource détectée")
        plt.axis('off')
        
        # Templates correspondants
        for i, res_name in enumerate(['barbarian'] + list(self.templates.keys())[1:], 4):
            plt.subplot(2, 3, i)
            template = self.templates[res_name][0]
            plt.imshow(cv2.cvtColor(template, cv2.COLOR_BGR2RGB))
            plt.title(res_name)
            plt.axis('off')
        
        plt.tight_layout()
        plt.show()
        
        return {
            'view': view_type,
            'resources': resources
        }

if __name__ == "__main__":
    detector = AdvancedViewDetector()
    
    # Analyse d'une capture
    test_image = os.path.join(detector.base_path, "explore_view.png")
    result = detector.analyze_screen(test_image)
    
    print("\nRésultats:")
    print(f"Type de vue: {result['view']}")
    print(f"Ressources: {', '.join(result['resources']) if result['resources'] else 'Aucune'}")