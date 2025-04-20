import cv2
import numpy as np

class ViewDetector:
    def __init__(self):
        # Points caractéristiques pour chaque vue (à calibrer)
        self.view_templates = {
            'ville': {
                'color': (40, 40, 200),  # BGR d'un élément UI spécifique
                'position': (50, 100),   # Position attendue
                'threshold': 0.9
            },
            'alentour': {
                'color': (80, 200, 40),
                'position': (1200, 100),
                'threshold': 0.85
            },
            # ... autres modes
        }

    def detect_current_view(self, screenshot):
        """Détecte le mode de vue actuel"""
        view_confidences = {}
        
        for view_name, params in self.view_templates.items():
            # Vérification couleur au point spécifié
            pixel_color = screenshot[params['position'][1], params['position'][0]]
            color_diff = np.linalg.norm(pixel_color - params['color'])
            confidence = 1 - (color_diff / 442)  # 442 = max distance couleur possible
            
            if confidence > params['threshold']:
                view_confidences[view_name] = confidence
                
        return max(view_confidences.items(), key=lambda x: x[1], default=('inconnu', 0))