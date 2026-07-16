import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))


from controllers.compra_controller import executar_compra

if __name__ == "__main__":
    executar_compra()