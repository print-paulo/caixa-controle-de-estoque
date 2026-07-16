import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from controllers.venda_controller import executar_venda

if __name__ == "__main__":
    executar_venda()