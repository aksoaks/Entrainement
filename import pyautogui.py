import pygetwindow as gw

# Trouver la fenêtre par son titre
window = gw.getWindowsWithTitle("Rise of Kingdoms")[0]
print(f"Position: {window.left}, {window.top} | Taille: {window.width}x{window.height}")