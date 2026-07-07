import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.excluir_produto import excluir_produto_permanente

from services.cadastrar_produto import (
    cadastrar_produto_base,
    adicionar_categoria,
    adicionar_codigo_barras_com_leitor,
    adicionar_quantidade,
    adicionar_medida_quantidade,
    adicionar_unidade,
    adicionar_valor_unitario
)

if __name__ == "__main__":

    while True:

        try:
            nome = input("Nome do produto: ").upper()
            categoria = input("Categoria: ").upper()

            # Cria o produto e obtém o ID
            id_produto = cadastrar_produto_base(nome)

            adicionar_categoria(id_produto, categoria)

            # Se aqui der erro, cai no except, e funciona a repetir caso use "sair"
            if not adicionar_codigo_barras_com_leitor(id_produto):
                excluir_produto_permanente(id_produto)
                print("Cadastro Cancelado")
                continue

            quantidade = int(input("Quantidade: "))
            medida = input("Medida da quantidade: ").upper()
            unidade = input("Unidade: ")
            valor = float(input("Valor unitário: "))

            adicionar_quantidade(id_produto, quantidade)
            adicionar_medida_quantidade(id_produto, medida)
            adicionar_unidade(id_produto, unidade)
            adicionar_valor_unitario(id_produto, valor)

            print(f"\nProduto cadastrado com sucesso! ID: {id_produto}")
            break

        except ValueError as e:

            print(f"\nErro: {e}")

            # Remove o cadastro incompleto
            if "id_produto" in locals():
                excluir_produto_permanente(id_produto)
                del id_produto
