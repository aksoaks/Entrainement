import cv2
import numpy as np
import os

class RobustViewDetector:
    def __init__(self):
        self.base_path = "D:/Users/Documents/Code/Python/Entrainement/tests/"
        
        # Configuration optimisée des zones
        self.config = {
            'city_logo': {
                'zone': (74, 903, 243, 1060),
                'color': [132, 83, 9],  # BGR
                'tolerance': 25  # Tolérance augmentée
            },
            'map_logo': {
                'zone': (74, 903, 243, 1060),
                'color': [140, 90, 20],  # BGR légèrement différent
                'tolerance': 25
            },
            'explore_marker': {
                'zone': (128, 494, 128, 494),  # Point unique
                'color': [195, 36, 246],  # BGR violet
                'tolerance': 15
            },
            'kingdom_logo': {
                'zone': (2037, 944, 2174, 1064),
                'color': [250, 200, 100],  # BGR
                'tolerance': 60  # Tolérance large
            },
            'mail_icon': {
                'zone': (1925, 971, 1983, 1028),
                'color': [150, 150, 150],  # BGR gris
                'tolerance': 40
            }
        }

    def _check_feature(self, img, feature_name):
        """Vérifie une caractéristique avec gestion d'erreur"""
        cfg = self.config.get(feature_name)
        if not cfg or 'zone' not in cfg:
            return False
            
        x1, y1, x2, y2 = cfg['zone']
        
        # Vérification des limites de l'image
        if any([coord >= img.shape[1] if i%2 == 0 else coord >= img.shape[0] 
               for i, coord in enumerate([x1, y1, x2, y2])]):
            return False
        
        # Pour les points uniques
        if x1 == x2 and y1 == y2:
            pixel = img[y1, x1]
            return np.all(np.abs(pixel - cfg['color']) <= cfg['tolerance'])
        
        # Pour les zones
        roi = img[y1:y2, x1:x2]
        if roi.size == 0:
            return False
            
        avg_color = np.mean(roi, axis=(0, 1))
        return np.all(np.abs(avg_color - cfg['color']) <= cfg['tolerance'])

    def detect_view(self, img):
        """Détection robuste avec logique améliorée"""
        if img is None:
            return 'unknown'
        
        # D'abord vérifier les vues complexes
        is_kingdom = (self._check_feature(img, 'kingdom_logo') and 
                     self._check_feature(img, 'mail_icon'))
        
        is_explore = (self._check_feature(img, 'city_logo') and 
                     self._check_feature(img, 'explore_marker'))
        
        if is_kingdom:
            return 'kingdom_view'
        if is_explore:
            return 'explore_view'
        
        # Ensuite différencier city/map
        if self._check_feature(img, 'city_logo'):
            # Comparaison précise des couleurs
            x, y = self.config['city_logo']['zone'][0:2]
            pixel = img[y, x]
            dist_city = np.sum(np.abs(pixel - self.config['city_logo']['color']))
            dist_map = np.sum(np.abs(pixel - self.config['map_logo']['color']))
            return 'city_view' if dist_city < dist_map else 'map_view'
        
        # Enfin vérifier map_logo seul
        if self._check_feature(img, 'map_logo'):
            return 'map_view'
            
        return 'unknown'

    def analyze_images(self):
        """Analyse toutes les images avec rapports détaillés"""
        views = ['city_view', 'map_view', 'explore_view', 'kingdom_view']
        
        for view in views:
            img_path = os.path.join(self.base_path, f"{view}.png")
            if not os.path.exists(img_path):
                print(f"Fichier manquant: {img_path}")
                continue
                
            img = cv2.imread(img_path)
            if img is None:
                print(f"Erreur de chargement: {img_path}")
                continue
                
            detected = self.detect_view(img)
            print(f"\nAnalyse de {view}.png:")
            print(f"=> Vue détectée: {detected}")
            
            # Vérification de toutes les features
            print("\nDétails des détections:")
            for feature in self.config:
                status = "DÉTECTÉ" if self._check_feature(img, feature) else "NON DÉTECTÉ"
                print(f"- {feature}: {status}")
            
            # Affichage avec annotations
            display_img = img.copy()
            for feature, cfg in self.config.items():
                x1, y1, x2, y2 = cfg['zone']
                detected = self._check_feature(img, feature)
                color = (0, 255, 0) if detected else (0, 0, 255)  # Vert ou rouge
                
                if x1 == x2 and y1 == y2:  # Point
                    cv2.circle(display_img, (x1, y1), 10, color, -1)
                else:  # Zone
                    cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 2)
                
                cv2.putText(display_img, feature, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            cv2.imshow(f"Résultats: {view}", display_img)
            cv2.waitKey(1000)  # Affichage pendant 1 seconde
        
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = RobustViewDetector()
    detector.analyze_images()