import sys
from pathlib import Path

# Ajoute le dossier parent au path Python
sys.path.append(str(Path(__file__).parent.parent))
from core.phone_controller import PhoneController