import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.cadastrar_produto import cadastrar_produto_base, adicionar_categoria, adicionar_codigo_barras_com_leitor, adicionar_quantidade, adicionar_medida_quantidade, adicionar_unidade, adicionar_valor_unitario
from utils.leitor_barras import codigo_lido


if __name__ == "__main__":
    # Teste rápido manual: cadastra o básico e vai completando campo a campo
    id_produto = cadastrar_produto_base(input("Nome do produto: "))
    adicionar_categoria(id_produto, input("Categoria: ").upper())
    adicionar_codigo_barras_com_leitor(id_produto)
    adicionar_quantidade(id_produto, int(input("Quantidade: ")))
    adicionar_medida_quantidade(id_produto, str(input("Medida da quantidade: ").upper()))
    adicionar_unidade(id_produto, input("Unidade: "))
    adicionar_valor_unitario(id_produto, float(input("Valor unitário: ")))
    print(f"Produto cadastrado com id {id_produto}")