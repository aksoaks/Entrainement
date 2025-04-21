import cv2
import numpy as np
from collections import defaultdict

class EnhancedViewDetector:
    def __init__(self):
        # Configuration flexible avec plages de couleurs
        self.features = {
            'city_logo': {
                'zone': (70, 900, 250, 1070),  # Marge ajoutée
                'color_range': {
                    'min': [120, 70, 0],   # BGR minimum
                    'max': [140, 100, 20]  # BGR maximum
                }
            },
            'explore_marker': {
                'zone': (120, 490, 135, 505),
                'color_range': {
                    'min': [180, 25, 230],
                    'max': [210, 45, 255]
                }
            },
            'kingdom_logo': {
                'zone': (2030, 940, 2180, 1070),
                'color_range': {
                    'min': [90, 180, 240],
                    'max': [110, 220, 260]
                }
            }
        }

    def _check_feature(self, img, feature_name):
        """Vérification avec plage de couleurs et similarité"""
        feat = self.features.get(feature_name)
        if not feat:
            return False
            
        x1, y1, x2, y2 = feat['zone']
        roi = img[y1:y2, x1:x2]
        
        if roi.size == 0:
            return False
            
        # Convertir en HSV pour une meilleure détection de couleur
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        avg_color = np.mean(hsv, axis=(0, 1))
        
        # Vérification dans la plage
        min_val = np.array(feat['color_range']['min'])
        max_val = np.array(feat['color_range']['max'])
        return np.all(avg_color >= min_val) and np.all(avg_color <= max_val)

    def detect_view(self, img):
        """Détection hiérarchique améliorée"""
        if img is None:
            return 'unknown'
        
        # D'abord vérifier les marqueurs uniques
        if self._check_feature(img, 'explore_marker'):
            return 'explore_view'
            
        if self._check_feature(img, 'kingdom_logo'):
            return 'kingdom_view'
            
        # Ensuite différencier city/map par similarité
        city_score = self._get_zone_similarity(img, 'city_logo')
        map_score = 0  # À implémenter si nécessaire
        
        if city_score > 0.7:  # Seuil ajustable
            return 'city_view'
            
        return 'unknown'

    def _get_zone_similarity(self, img, feature_name):
        """Retourne un score de similarité [0-1]"""
        feat = self.features.get(feature_name)
        if not feat:
            return 0
            
        x1, y1, x2, y2 = feat['zone']
        roi = img[y1:y2, x1:x2]
        
        if roi.size == 0:
            return 0
            
        # Calcul de la distance colorimétrique normalisée
        avg_color = np.mean(roi, axis=(0, 1))
        target = np.array(feat['color_range']['min']) + np.array(feat['color_range']['max']) / 2
        distance = np.linalg.norm(avg_color - target)
        max_distance = np.linalg.norm([255, 255, 255])
        
        return 1 - (distance / max_distance)