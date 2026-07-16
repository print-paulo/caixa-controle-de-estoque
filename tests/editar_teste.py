import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.editar_produto import executar_edicao

if __name__ == "__main__":
    executar_edicao()