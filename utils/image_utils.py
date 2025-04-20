import cv2
import pytesseract
import numpy as np
import re

def detect_loading_percentage(image, roi_coords):
    """Détecte le pourcentage de chargement (déplacé depuis game_loader.py)"""
    try:
        x, y, w, h = roi_coords
        roi = image[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        mask = cv2.inRange(blurred, 180, 255)
        kernel = np.ones((2, 2), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        custom_config = r'--psm 7 --oem 3 -l fra+eng'
        text = pytesseract.image_to_string(mask, config=custom_config).strip()
        
        match = re.search(r'(\d{1,3})\s*%', text)
        return int(match.group(1)) if match else None
        
    except Exception as e:
        print(f"Erreur détection: {str(e)}")
        return None