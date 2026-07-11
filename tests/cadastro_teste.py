import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.cadastrar_produto import executar_cadastro


if __name__ == "__main__":
    executar_cadastro()