import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from controllers.produto_controller import executar_busca

if __name__ == "__main__":
    executar_busca()