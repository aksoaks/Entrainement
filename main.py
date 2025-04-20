from game_loader import GameLoader

if __name__ == "__main__":
    print("Démarrage du système de chargement...")
    loader = GameLoader()
    
    if loader.wait_for_loading() == 1:
        print("✅ Jeu entièrement chargé!")
    else:
        print("❌ Échec du chargement")