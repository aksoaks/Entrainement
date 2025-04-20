#import du path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.phone_controller import PhoneController

import cv2

phone = PhoneController()
views = ['ville', 'alentour','intermediaire', 'royaume']  # etc.

for view in views:
    input(f"Placez-vous en mode {view} puis appuyez sur Entrée...")
    img = phone.capture_screen(f"{view}_reference.png")
    
    # Afficher un point cliquable pour sélectionner le pixel caractéristique
    cv2.imshow(view, img)
    cv2.setMouseCallback(view, lambda e,x,y,_,__: print(f"Pixel ({x},{y}): {img[y,x]}"))
    cv2.waitKey(3000)
    cv2.destroyAllWindows()