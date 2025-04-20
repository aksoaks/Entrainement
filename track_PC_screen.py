import pygetwindow as gw
import pyautogui
import tkinter as tk
from tkinter import ttk
import threading
import queue
from pynput import mouse
import time

class AdvancedMouseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Tracker Souris Avancé")
        self.root.geometry("700x500")
        
        # Configuration
        self.stop_event = threading.Event()
        self.tracking_active = False
        self.update_interval = 0.1  # 100ms entre les updates
        self.last_update_time = 0
        self.scroll_active = False
        
        # Initialisation
        self.init_game_window()
        self.setup_advanced_ui()
        self.start_enhanced_mouse_listener()
        
        print(f"Fenêtre jeu détectée - Position: ({self.win_left}, {self.win_top}) Taille: {self.win_width}x{self.win_height}")

    def init_game_window(self):
        """Détection de la fenêtre du jeu"""
        try:
            game_window = gw.getWindowsWithTitle("Rise of Kingdoms")[0]
            self.win_left = game_window.left
            self.win_top = game_window.top
            self.win_width = game_window.width
            self.win_height = game_window.height
        except:
            screen_width, screen_height = pyautogui.size()
            self.win_left, self.win_top, self.win_width, self.win_height = 0, 0, screen_width, screen_height

    def setup_advanced_ui(self):
        """Interface améliorée"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panneau de contrôle
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Start Tracking", command=self.start_tracking).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Stop Tracking", command=self.stop_tracking).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Log", command=self.clear_tracking).pack(side=tk.RIGHT, padx=5)
        
        # Zone de logs avec scrollbar
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tracking_log = tk.Text(log_frame, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        self.tracking_log.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.tracking_log.yview)
        
        # Statistiques
        self.stats_frame = ttk.Frame(main_frame)
        self.stats_frame.pack(fill=tk.X)
        
        self.stats_label = ttk.Label(self.stats_frame, text="Statut: Prêt | Événements: 0")
        self.stats_label.pack()
        
        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X)
        
        ttk.Checkbutton(options_frame, text="Tracker scroll", variable=tk.BooleanVar(value=True)).pack(side=tk.LEFT)
        ttk.Checkbutton(options_frame, text="Afficher releases", variable=tk.BooleanVar(value=True)).pack(side=tk.LEFT)

    def start_enhanced_mouse_listener(self):
        """Listener avec gestion complète des événements"""
        def on_move(x, y):
            if self.tracking_active and time.time() - self.last_update_time > self.update_interval:
                self.last_update_time = time.time()
                self.log_event(f"MOVE: X={x-self.win_left}, Y={y-self.win_top}")

        def on_click(x, y, button, pressed):
            action = "PRESS" if pressed else "RELEASE"
            self.log_event(f"{action} {button.name}: X={x-self.win_left}, Y={y-self.win_top}")

        def on_scroll(x, y, dx, dy):
            direction = "UP" if dy > 0 else "DOWN"
            self.log_event(f"SCROLL {direction}: X={x-self.win_left}, Y={y-self.win_top}")

        self.listener = mouse.Listener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll
        )
        self.listener.start()

    def log_event(self, message):
        """Journalisation des événements avec timestamp"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.tracking_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.tracking_log.see(tk.END)
        self.update_stats()

    def update_stats(self):
        """Mise à jour des statistiques"""
        line_count = self.tracking_log.index('end-1c').split('.')[0]
        self.stats_label.config(text=f"Statut: {'Actif' if self.tracking_active else 'Inactif'} | Événements: {line_count}")

    def start_tracking(self):
        self.tracking_active = True
        self.log_event("==== TRACKING STARTED ====")
        self.update_stats()

    def stop_tracking(self):
        self.tracking_active = False
        self.log_event("==== TRACKING STOPPED ====")
        self.update_stats()

    def clear_tracking(self):
        self.tracking_log.delete(1.0, tk.END)
        self.update_stats()

    def on_close(self):
        self.stop_event.set()
        if hasattr(self, 'listener'):
            self.listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    tracker = AdvancedMouseTracker(root)
    root.protocol("WM_DELETE_WINDOW", tracker.on_close)
    root.mainloop()