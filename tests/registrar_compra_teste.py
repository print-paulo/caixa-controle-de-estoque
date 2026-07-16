import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.leitor_barras import codigo_lido
from services.buscar_produto import buscar_por_codigo_barras
from services.registrar_compra import (
    iniciar_compra,
    adicionar_item_compra,
    calcular_total_compra,
    finalizar_compra,
    cancelar_compra,
)

from controllers.compra_controller import executar_compra

if __name__ == "__main__":
    executar_compra()