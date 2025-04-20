import time
import json
from datetime import datetime
import os

class CalibrationRecorder:
    def __init__(self):
        self.actions = []
        self.calibration_data = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("calibration_data", exist_ok=True)
    
    def record_action(self, action_type, coordinates=None, details=None):
        """Enregistre une action utilisateur"""
        action = {
            "timestamp": time.time(),
            "type": action_type,
            "coordinates": coordinates,
            "details": details
        }
        self.actions.append(action)
    
    def save_calibration(self, mode_name, pixel_data):
        """Sauvegarde les données de calibration avec les actions associées"""
        calibration_entry = {
            "mode": mode_name,
            "timestamp": datetime.now().isoformat(),
            "actions": self.actions.copy(),
            "pixel_data": pixel_data
        }
        self.calibration_data.append(calibration_entry)
        self.actions.clear()  # Réinitialise les actions pour le prochain mode
        
        # Sauvegarde dans un fichier séparé
        filename = f"calibration_data/{mode_name}_{self.session_id}_{len(self.calibration_data)}.json"
        with open(filename, 'w') as f:
            json.dump(calibration_entry, f, indent=2)
        
        return filename

# Exemple d'utilisation dans votre script
if __name__ == "__main__":
    recorder = CalibrationRecorder()
    
    # Simulation d'actions utilisateur avant la calibration "ville"
    recorder.record_action("tap", coordinates=(100, 200))
    recorder.record_action("swipe", details={"direction": "left", "distance": 300})
    
    # Simulation de la capture des pixels
    ville_pixels = [
        {"coord": (2242, 703), "rgb": [105, 178, 124]},
        {"coord": (2241, 703), "rgb": [104, 177, 127]}
    ]
    
    # Sauvegarde
    saved_file = recorder.save_calibration("ville", ville_pixels)
    print(f"Calibration sauvegardée dans {saved_file}")