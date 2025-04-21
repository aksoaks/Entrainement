import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import queue
import re
from datetime import datetime
import math
import time

class EnhancedGestureTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Gesture Tracker")
        self.root.geometry("1100x850")
        
        # Configuration
        self.device_id = "BPN7N18A25003148"
        self.tracking = False
        self.process = None
        self.event_queue = queue.Queue()
        
        # Suivi des doigts
        self.fingers = {}
        self.last_gesture = None
        self.last_distance = None
        self.gesture_start_time = 0
        self.last_tap_time = 0
        
        # Paramètres réglables
        self.ZOOM_THRESHOLD = 1.15  # 15% d'augmentation
        self.DEZOOM_THRESHOLD = 0.85  # 15% de diminution
        self.TAP_MAX_DURATION = 0.3  # 300ms max pour un tap
        self.MIN_GESTURE_DURATION = 0.2  # 200ms min pour valider un geste
        
        # Interface
        self.create_ui()
        self.check_queue()
        
    def create_ui(self):
        """Interface améliorée avec plus de contrôles"""
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panneau de contrôle
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # Boutons
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(side=tk.LEFT)
        
        self.start_btn = tk.Button(btn_frame, text="Start", command=self.start_capture, 
                                 bg='#2E7D32', fg='white', width=10)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="Stop", command=self.stop_capture,
                                bg='#C62828', fg='white', width=10, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Paramètres
        settings_frame = tk.Frame(control_frame)
        settings_frame.pack(side=tk.RIGHT)
        
        tk.Label(settings_frame, text="Zoom Threshold:").pack(side=tk.LEFT)
        self.zoom_thresh = tk.Scale(settings_frame, from_=1.05, to=1.3, resolution=0.01,
                                  orient=tk.HORIZONTAL, length=150)
        self.zoom_thresh.set(self.ZOOM_THRESHOLD)
        self.zoom_thresh.pack(side=tk.LEFT, padx=5)
        
        tk.Label(settings_frame, text="Dezoom Threshold:").pack(side=tk.LEFT)
        self.dezoom_thresh = tk.Scale(settings_frame, from_=0.7, to=0.95, resolution=0.01,
                                    orient=tk.HORIZONTAL, length=150)
        self.dezoom_thresh.set(self.DEZOOM_THRESHOLD)
        self.dezoom_thresh.pack(side=tk.LEFT, padx=5)
        
        # Visualisation
        self.canvas = tk.Canvas(main_frame, bg='#111', height=250)
        self.canvas.pack(fill=tk.X, pady=(0, 10))
        
        # Affichage du geste
        self.gesture_var = tk.StringVar(value="En attente de geste...")
        gesture_display = tk.Label(main_frame, textvariable=self.gesture_var,
                                 font=('Arial', 12, 'bold'), fg='#FFC107')
        gesture_display.pack()
        
        # Logs
        self.log_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=130,
            height=25,
            font=('Consolas', 9),
            bg='#111',
            fg='white')
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
    def clear_logs(self):
        self.log_area.delete(1.0, tk.END)
        
    def log(self, message, level="INFO"):
        """Journalisation avec coloration"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        color = {
            "INFO": "#4CAF50",
            "WARNING": "#FFC107",
            "ERROR": "#F44336",
            "DEBUG": "#2196F3",
            "TAP": "#9C27B0"
        }.get(level, "white")
        
        self.log_area.tag_config(level, foreground=color)
        self.log_area.insert(tk.END, f"[{timestamp}] ", level)
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        
    def check_queue(self):
        """Traite les événements en file d'attente"""
        while not self.event_queue.empty():
            event = self.event_queue.get()
            self.process_event(event)
        self.root.after(50, self.check_queue)
        
    def start_capture(self):
        """Démarre la capture des événements"""
        if self.tracking:
            return
            
        self.tracking = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.clear_logs()
        self.log("Démarrage de la capture...", "INFO")
        
        # Mise à jour des paramètres
        self.ZOOM_THRESHOLD = float(self.zoom_thresh.get())
        self.DEZOOM_THRESHOLD = float(self.dezoom_thresh.get())
        
        threading.Thread(target=self.capture_events, daemon=True).start()
        
    def stop_capture(self):
        """Arrête la capture"""
        self.tracking = False
        if self.process:
            self.process.terminate()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Capture arrêtée", "INFO")
        
    def capture_events(self):
        """Capture les événements bruts via ADB"""
        try:
            self.process = subprocess.Popen(
                ["adb", "-s", self.device_id, "shell", "getevent", "-lt", "/dev/input/event3"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1)
                
            current_event = {}
            last_down_time = 0
                
            while self.tracking:
                line = self.process.stdout.readline()
                if not line:
                    continue
                    
                # Extraction des données d'événement
                if "add device" in line or "name:" in line:
                    continue
                    
                parts = line.strip().split()
                if len(parts) < 4:
                    continue
                    
                timestamp = parts[0].strip('[]')
                event_type = parts[2]
                event_code = parts[3]
                value = parts[4] if len(parts) > 4 else None
                
                # Détection des taps (BTN_TOUCH DOWN/UP rapides)
                if event_code == "BTN_TOUCH":
                    if value == "DOWN":
                        last_down_time = time.time()
                    elif value == "UP":
                        if last_down_time and (time.time() - last_down_time) <= self.TAP_MAX_DURATION:
                            self.event_queue.put({"TAP": True})
                
                # Construction de l'événement complet
                if event_code == "SYN_REPORT":
                    if current_event:
                        self.event_queue.put(current_event)
                        current_event = {}
                else:
                    current_event[event_code] = value
                    current_event["timestamp"] = timestamp
                    
        except Exception as e:
            self.event_queue.put({"ERROR": str(e)})
        finally:
            self.stop_capture()
            
    def process_event(self, event):
        """Analyse les événements pour détecter les gestes"""
        if "ERROR" in event:
            self.log(f"Erreur: {event['ERROR']}", "ERROR")
            return
            
        if "TAP" in event:
            self.handle_tap()
            return
            
        # Mise à jour des positions des doigts
        if "ABS_MT_TRACKING_ID" in event:
            finger_id = event["ABS_MT_TRACKING_ID"]
            if finger_id not in self.fingers:
                self.fingers[finger_id] = {"first_seen": time.time()}
            else:
                self.fingers[finger_id]["last_seen"] = time.time()
                
        if "ABS_MT_POSITION_X" in event and "ABS_MT_TRACKING_ID" in event:
            finger_id = event["ABS_MT_TRACKING_ID"]
            self.fingers[finger_id]["x"] = int(event["ABS_MT_POSITION_X"], 16)
            
        if "ABS_MT_POSITION_Y" in event and "ABS_MT_TRACKING_ID" in event:
            finger_id = event["ABS_MT_TRACKING_ID"]
            self.fingers[finger_id]["y"] = int(event["ABS_MT_POSITION_Y"], 16)
            
        # Nettoyage des doigts qui ne sont plus détectés
        current_time = time.time()
        to_remove = [fid for fid, fdata in self.fingers.items() 
                    if current_time - fdata.get("last_seen", current_time) > 0.3]
        for fid in to_remove:
            self.fingers.pop(fid, None)
            
        # Détection des gestes
        if len(self.fingers) == 1:
            self.detect_single_touch()
        elif len(self.fingers) >= 2:
            self.detect_multi_touch()
        else:
            self.gesture_var.set("Aucun geste détecté")
            self.last_gesture = None
            self.last_distance = None
            self.update_canvas()
            
    def handle_tap(self):
        """Gère la détection d'un tap"""
        if time.time() - self.last_tap_time > 0.5:  # Anti-rebond
            self.log("Tap détecté", "TAP")
            self.gesture_var.set("TAP détecté")
            self.last_tap_time = time.time()
            self.update_canvas()
            self.root.after(500, lambda: self.gesture_var.set("Prêt"))
            
    def detect_single_touch(self):
        """Détection des gestes à un doigt"""
        finger = next(iter(self.fingers.values()))
        x, y = finger.get("x", 0), finger.get("y", 0)
        
        self.gesture_var.set(f"Touch: X={x}, Y={y}")
        self.update_canvas()
        
    def detect_multi_touch(self):
        """Détection des gestes multi-touch avec anti-faux positifs"""
        fingers = list(self.fingers.values())
        if len(fingers) < 2:
            return
            
        # Calcul de la distance actuelle
        x1, y1 = fingers[0].get("x", 0), fingers[0].get("y", 0)
        x2, y2 = fingers[1].get("x", 0), fingers[1].get("y", 0)
        current_distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        
        # Vérification de la durée du geste
        gesture_duration = time.time() - min(f["first_seen"] for f in fingers)
        
        if self.last_distance is not None and gesture_duration > self.MIN_GESTURE_DURATION:
            ratio = current_distance / self.last_distance
            
            if ratio > self.ZOOM_THRESHOLD and self.last_gesture != "ZOOM":
                self.gesture_var.set("ZOOM (écartement)")
                self.log(f"Zoom détecté (ratio: {ratio:.2f})", "INFO")
                self.last_gesture = "ZOOM"
            elif ratio < self.DEZOOM_THRESHOLD and self.last_gesture != "DEZOOM":
                self.gesture_var.set("DÉZOOM (pincement)")
                self.log(f"Dézoom détecté (ratio: {ratio:.2f})", "INFO")
                self.last_gesture = "DEZOOM"
                
        self.last_distance = current_distance
        self.update_canvas()
        
    def update_canvas(self):
        """Met à jour la visualisation sur le canvas"""
        self.canvas.delete("all")
        
        # Affiche les doigts
        for i, (fid, finger) in enumerate(self.fingers.items()):
            x = finger.get("x", 0)
            y = finger.get("y", 0)
            
            # Normalisation pour l'affichage
            disp_x = x * self.canvas.winfo_width() // 32768
            disp_y = y * self.canvas.winfo_height() // 32768
            
            color = "#FF5252" if i == 0 else "#448AFF"
            self.canvas.create_oval(disp_x-15, disp_y-15, disp_x+15, disp_y+15, 
                                   fill=color, outline='white')
            self.canvas.create_text(disp_x, disp_y-20, text=f"ID: {fid}", fill='white')
            
        # Affiche la distance pour deux doigts
        if len(self.fingers) == 2:
            fingers = list(self.fingers.values())
            x1 = fingers[0].get("x", 0) * self.canvas.winfo_width() // 32768
            y1 = fingers[0].get("y", 0) * self.canvas.winfo_height() // 32768
            x2 = fingers[1].get("x", 0) * self.canvas.winfo_width() // 32768
            y2 = fingers[1].get("y", 0) * self.canvas.winfo_height() // 32768
            
            self.canvas.create_line(x1, y1, x2, y2, fill="#FFEB3B", width=2, dash=(3,3))
            
            # Affiche la distance
            mid_x, mid_y = (x1+x2)//2, (y1+y2)//2
            distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            self.canvas.create_text(mid_x, mid_y, text=f"{distance:.1f}px", 
                                  fill="white", font=('Arial', 10, 'bold'))

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedGestureTracker(root)
    root.mainloop()