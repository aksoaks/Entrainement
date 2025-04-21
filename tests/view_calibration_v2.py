import cv2
import numpy as np
import subprocess
import tkinter as tk
from threading import Thread
import time
from queue import Queue
import logging

# Initialiser le logging
logging.basicConfig(filename='actions_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# Capture via adb (optimisé en utilisant directement la mémoire)
def capture_screen_via_adb():
    process = subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True)
    return np.frombuffer(process.stdout, np.uint8)

# Fonction de détection optimisée
def detect_view(image_data, templates, threshold=0.8, violet_threshold=0.7):
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    if image is None:
        print("Erreur: Impossible de charger l'image")
        return None, None

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    results = {}

    # Optimiser la détection en travaillant sur des zones spécifiques
    for view_name, template_info in templates.items():
        template_path = template_info['path']
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            continue

        search_area = gray_image
        search_offset = (0, 0)

        # Limiter les zones à analyser (comme pour le mail_button)
        if view_name == 'explore_marker':
            x1, y1, x2, y2 = 85, 449, 354, 528
            search_area = gray_image[y1:y2, x1:x2]
            search_offset = (x1, y1)

        if view_name == 'mail_button':
            x1, y1, x2, y2 = 1922, 971, 1984, 1027
            search_area = gray_image[y1:y2, x1:x2]
            search_offset = (x1, y1)

        # Utilisation d'un seuil de confiance plus élevé pour éviter les faux positifs
        res = cv2.matchTemplate(search_area, cv2.cvtColor(template, cv2.COLOR_BGR2GRAY), cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        max_loc = (max_loc[0] + search_offset[0], max_loc[1] + search_offset[1])

        violet_percent = 0
        if template_info.get('check_violet', False):
            x, y = max_loc
            w, h = template.shape[1], template.shape[0]
            roi = image[y:y+h, x:x+w]
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            lower_violet = np.array([130, 50, 50])
            upper_violet = np.array([160, 255, 255])
            mask = cv2.inRange(hsv, lower_violet, upper_violet)
            violet_percent = np.sum(mask > 0) / (w * h)

        detected = max_val >= threshold
        if template_info.get('check_violet', False):
            detected = detected and (violet_percent >= violet_threshold)

        results[view_name] = {
            'detected': bool(detected),
            'confidence': float(max_val),
            'violet_percent': float(violet_percent),
            'location': max_loc
        }

    return results, image

# Fonction pour déterminer la vue
def determine_final_view(detected):
    if not detected['goto_city']['detected'] and detected['goto_map']['detected'] and not detected['explore_marker']['detected'] and not detected['mail_button']['detected']:
        return "city_view"
    elif detected['goto_city']['detected'] and not detected['goto_map']['detected'] and detected['explore_marker']['detected'] and not detected['mail_button']['detected']:
        return "explore_view"
    elif detected['goto_city']['detected'] and not detected['goto_map']['detected'] and not detected['explore_marker']['detected'] and not detected['mail_button']['detected']:
        return "map_view"
    elif detected['goto_city']['detected'] and not detected['goto_map']['detected'] and detected['explore_marker']['detected'] and detected['mail_button']['detected']:
        return "kingdom_view"
    else:
        return "unknown"

# Fonction pour loguer les actions de l'utilisateur
def log_user_action(action, view):
    logging.info(f"Action: {action} - Vue détectée: {view}")

# Fonction pour mesurer la latence entre deux détections
last_detection_time = None
latency = 0

def measure_latency():
    global last_detection_time, latency
    current_time = time.time()

    # Si une action manuelle a été effectuée, on mesure la latence
    if last_detection_time is not None:
        latency = current_time - last_detection_time
        logging.info(f"Latence de détection: {latency:.4f} secondes")

    last_detection_time = current_time

# Fonction principale pour Tkinter
def main_loop():
    templates = {
        'goto_city': {
            'path': 'tests/templates/goto_city.png',
            'check_violet': False
        },
        'goto_map': {
            'path': 'tests/templates/goto_map.png',
            'check_violet': False
        },
        'explore_marker': {
            'path': 'tests/templates/explore_marker.png',
            'check_violet': True
        },
        'mail_button': {
            'path': 'tests/templates/mail_button.png',
            'check_violet': False
        }
    }

    # Fenêtre Tkinter
    root = tk.Tk()
    root.title("Vue Actuelle")
    label = tk.Label(root, font=("Helvetica", 24))
    label.pack()

    # File d'attente pour stocker les images capturées
    capture_queue = Queue()

    # Thread pour la capture continue des images
    def capture_thread():
        while True:
            image_data = capture_screen_via_adb()
            capture_queue.put(image_data)
            time.sleep(0.05)  # Fréquence de capture des images (environ toutes les 50 ms)

    # Thread pour le traitement des images capturées
    def process_thread():
        while True:
            if not capture_queue.empty():
                image_data = capture_queue.get()
                detected, _ = detect_view(image_data, templates)
                if detected:
                    view = determine_final_view(detected)
                    label.config(text=f"Vue détectée: {view}")
                    
                    # Si une action manuelle est effectuée, on logue et mesure la latence
                    log_user_action("Vue détectée", view)
                    measure_latency()
            time.sleep(0.05)  # Fréquence de traitement des images

    # Lancer les threads de capture et de traitement
    capture_thread_instance = Thread(target=capture_thread, daemon=True)
    capture_thread_instance.start()

    process_thread_instance = Thread(target=process_thread, daemon=True)
    process_thread_instance.start()

    root.mainloop()

if __name__ == "__main__":
    main_loop()
