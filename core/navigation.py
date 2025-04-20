class NavigationController:
    def __init__(self, phone):
        self.phone = phone
        self.view_actions = {
            'ville': {'tap': (1200, 700)},  # Bouton monde
            'alentour': {'tap': (100, 100)}, # Bouton ville
            # ...
        }

    def switch_view(self, target_view):
        """Change de mode de vue"""
        current_view = ViewDetector().detect_current_view(self.phone.capture_screen())
        
        while current_view != target_view:
            action = self.view_actions.get(current_view)
            self.phone.tap(*action['tap'])
            time.sleep(2)  # Temps de transition
            current_view = ViewDetector().detect_current_view(self.phone.capture_screen())