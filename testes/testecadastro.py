import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.cadastrar_produto import cadastrar_produto
from utils.leitor_barras import codigo_lido


if __name__ == "__main__":
    id_produto = cadastrar_produto(
        nome_produto=input("Insira o nome do produto ").strip(),
        categoria=input("Insira o categoria ").strip(),
        quantidade= int(input("Insira o quantidade ")),
        medida_quantidade=float(input("Insira o medida quantidade ")),
        unidade=str(input("Insira o unidade ")),
        valor_unitario=float(input("Insira o valor unitario ")),
        estoque_deposito=int(input("Insira o estoque deposito ")),
        estoque_minimo=int(input("Insira o estoque minimo ")),
        codigo_barras=codigo_lido()
    )
    print(f"Produto cadastrado com id {id_produto}")