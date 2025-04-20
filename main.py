from game_loader import GameLoader
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Initialisation du système...")
    loader = GameLoader()
    
    if loader.wait_for_loading() == 1:
        logging.info("Jeu complètement chargé!")
    else:
        logging.error("Échec du chargement")

if __name__ == "__main__":
    main()