import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.leitor_barras import codigo_lido
from services.buscar_produto import buscar_por_codigo_barras
from services.registrar_venda import (
    iniciar_venda,
    adicionar_item_venda,
    calcular_total_venda,
    finalizar_venda,
    cancelar_venda,
)

if __name__ == "__main__":

    id_venda = iniciar_venda()
    print(f"\nVenda {id_venda} aberta. Passe os produtos (ou digite 'sair' pra fechar a venda).\n")

    total_itens = 0

    while True:
        codigo = codigo_lido()

        if codigo is None:
            break

        produto = buscar_por_codigo_barras(codigo)
        if produto is None:
            print("Produto não encontrado ou inativo.\n")
            continue

        nome_produto = produto[4]  # coluna nome_produto

        try:
            quantidade = int(input(f"Quantidade de '{nome_produto}': "))
        except ValueError:
            print("Quantidade inválida, tente novamente.\n")
            continue

        try:
            sub_total = adicionar_item_venda(id_venda, codigo, quantidade)
            total_itens += 1
            print(f"Adicionado: {quantidade}x {nome_produto} = R$ {sub_total:.2f}\n")
        except ValueError as e:
            print(f"Erro: {e}\n")

    if total_itens == 0:
        cancelar_venda(id_venda)
        print("Nenhum item adicionado. Venda cancelada.")
        sys.exit()

    total = calcular_total_venda(id_venda)
    print(f"\nTotal da venda: R$ {total:.2f}")

    confirmar = input("Finalizar venda? (s/n): ").strip().lower()

    if confirmar != "s":
        cancelar_venda(id_venda)
        print("Venda cancelada. Estoque devolvido.")
        sys.exit()

    forma_pagamento = input("Forma de pagamento (dinheiro/cartao/pix): ").strip().lower()

    try:
        total_final = finalizar_venda(id_venda, forma_pagamento)
        print(f"\nVenda {id_venda} finalizada com sucesso!")
        print(f"Forma de pagamento: {forma_pagamento}")
        print(f"Total: R$ {total_final:.2f}")
    except ValueError as e:
        print(f"Erro ao finalizar venda: {e}")