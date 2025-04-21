from PIL import Image
from pathlib import Path

# Charger l'image
image_path = Path("D:/Users/Documents/Code/Python/Entrainement/tests/kingdom_view.png")
image = Image.open(image_path)

# Coordonnées du rectangle à garder (coin supérieur gauche et coin inférieur droit)
x1, y1 = 1926, 975
x2, y2 = 1986, 1027

# Rogner l'image
cropped_picture = image.crop((x1, y1, x2, y2))

# Sauvegarder l'image rognée
cropped_picture.save(r"D:\Users\Documents\Code\Python\Entrainement\tests\templates\mail_button.png")
