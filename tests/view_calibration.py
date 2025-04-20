import cv2
import numpy as np
import os
from matplotlib import pyplot as plt

class AdvancedViewDetector:
    def __init__(self):
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        self.template_path = os.path.join(self.base_path, "templates/")
        
        # Chargement des templates avec vérification
        self.templates = {}
        template_files = ['barbarian.png', 'food.png', 'gems.png', 'gold.png', 'stone.png', 'wood.png']
        for file in template_files:
            try:
                path = os.path.join(self.template_path, file)
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    if img.shape[2] == 4:  # Avec canal alpha
                        self.templates[file.split('.')[0]] = (img[:,:,:3], img[:,:,3])
                    else:
                        self.templates[file.split('.')[0]] = (img, None)
            except Exception as e:
                print(f"Erreur chargement {file}: {str(e)}")

        # Configuration des vues simplifiée
        self.view_config = {
            'city_view': {
                'logo_zone': (74, 903, 243, 1060),
                'color': [132, 83, 9],  # BGR exact du screenshot
                'tolerance': 15
            },
            'map_view': {
                'logo_zone': (74, 903, 243, 1060),
                'color': [132, 83, 9],
                'tolerance': 15
            },
            'explore_view': {
                'special_marker': (125, 501, [197, 34, 251], 10)  # x, y, BGR, tolérance
            },
            'kingdom_view': {
                'logo_zone': (2037, 944, 2174, 1064),
                'color': [100, 200, 250],
                'tolerance': 50
            }
        }

    def _match_template(self, img, template_data):
        """Correspondance de template optimisée"""
        template, alpha = template_data
        method = cv2.TM_CCOEFF_NORMED
        
        try:
            if alpha is not None:
                mask = cv2.merge([alpha, alpha, alpha])
                res = cv2.matchTemplate(img, template, method, mask=mask)
            else:
                res = cv2.matchTemplate(img, template, method)
            return cv2.minMaxLoc(res)[1]  # Retourne le score max
        except Exception:
            return 0.0

    def detect_view(self, img):
        """Détection robuste de la vue"""
        if img is None:
            return None
        
        # 1. Vérifier kingdom_view en premier
        if 'kingdom_view' in self.view_config:
            zone = self.view_config['kingdom_view'].get('logo_zone')
            if zone:
                x1, y1, x2, y2 = zone
                if y2 <= img.shape[0] and x2 <= img.shape[1]:
                    roi = img[y1:y2, x1:x2]
                    avg_color = np.mean(roi, axis=(0, 1))
                    expected = self.view_config['kingdom_view'].get('color')
                    tol = self.view_config['kingdom_view'].get('tolerance', 50)
                    if expected and np.all(np.abs(avg_color - expected) <= tol):
                        return 'kingdom_view'

        # 2. Vérifier explore_view (marqueur violet + barbares)
        if 'explore_view' in self.view_config and 'special_marker' in self.view_config['explore_view']:
            x, y, expected_color, tol = self.view_config['explore_view']['special_marker']
            if y < img.shape[0] and x < img.shape[1]:
                pixel = img[y, x]
                if np.all(np.abs(pixel - expected_color) <= tol):
                    if 'barbarian' in self.templates:
                        score = self._match_template(img, self.templates['barbarian'])
                        if score > 0.8:
                            return 'explore_view'

        # 3. Différencier city_view et map_view
        if 'city_view' in self.view_config and 'logo_zone' in self.view_config['city_view']:
            zone = self.view_config['city_view']['logo_zone']
            x1, y1, x2, y2 = zone
            if y2 <= img.shape[0] and x2 <= img.shape[1]:
                roi = img[y1:y2, x1:x2]
                avg_color = np.mean(roi, axis=(0, 1))
                expected = self.view_config['city_view'].get('color')
                tol = self.view_config['city_view'].get('tolerance', 15)
                if expected and np.all(np.abs(avg_color - expected) <= tol):
                    return 'city_view'
        
        return 'map_view'

    def analyze_resources(self, img):
        """Détection des ressources avec templates"""
        resources = []
        if img is None:
            return resources
            
        for res_name, template_data in self.templates.items():
            if res_name == 'barbarian':
                continue  # Déjà utilisé pour explore_view
                
            score = self._match_template(img, template_data)
            if score > 0.8:
                resources.append(res_name)
        return resources

    def visualize_detection(self, img_path):
        """Visualisation claire des résultats"""
        img = cv2.imread(img_path)
        if img is None:
            print(f"Impossible de charger {img_path}")
            return
            
        view_type = self.detect_view(img)
        resources = self.analyze_resources(img)
        
        plt.figure(figsize=(15, 6))
        
        # Image originale avec annotations
        plt.subplot(1, 2, 1)
        display_img = img.copy()
        
        # Annoter selon la vue détectée
        if view_type == 'kingdom_view':
            zone = self.view_config['kingdom_view']['logo_zone']
            cv2.rectangle(display_img, (zone[0], zone[1]), (zone[2], zone[3]), (0, 255, 0), 2)
            cv2.putText(display_img, 'Kingdom View', (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        elif view_type == 'explore_view':
            x, y, _, _ = self.view_config['explore_view']['special_marker']
            cv2.circle(display_img, (x, y), 10, (255, 0, 255), -1)
            cv2.putText(display_img, 'Explore View', (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
            
            # Dessiner la zone barbare si détectée
            if 'barbarian' in self.templates:
                template, _ = self.templates['barbarian']
                res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                if max_val > 0.8:
                    h, w = template.shape[:2]
                    cv2.rectangle(display_img, max_loc, (max_loc[0]+w, max_loc[1]+h), (0, 0, 255), 2)
        
        plt.imshow(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
        plt.title(f"Vue détectée: {view_type}")
        plt.axis('off')
        
        # Liste des ressources
        plt.subplot(1, 2, 2)
        if resources:
            plt.text(0.1, 0.5, "\n".join(resources), fontsize=12)
        else:
            plt.text(0.1, 0.5, "Aucune ressource détectée", fontsize=12)
        plt.title("Ressources détectées")
        plt.axis('off')
        
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    detector = AdvancedViewDetector()
    
    # Test sur les différentes vues
    test_images = {
        'city_view': 'city_view.png',
        'map_view': 'map_view.png',
        'explore_view': 'explore_view.png',
        'kingdom_view': 'kingdom_view.png'
    }
    
    for view_name, img_file in test_images.items():
        print(f"\nAnalyse de {view_name}...")
        img_path = os.path.join(detector.base_path, img_file)
        detector.visualize_detection(img_path)