import sys
from pathlib import Path

# Takto zabezpečíme, aby bol koreňový adresár projektu pridaný do sys.path pri spúšťaní testov z adresára tests/.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
