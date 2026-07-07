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
from tests.cadastro_teste import executar_cadastro

if __name__ == "__main__":

    fornecedor = input("Nome do fornecedor (ou deixe em branco): ").strip() or None
    id_compra = iniciar_compra(fornecedor)

    print(f"\nCompra {id_compra} aberta. Passe os produtos recebidos (ou digite 'sair' pra fechar a compra).\n")

    total_itens = 0

    while True:
        codigo = codigo_lido()

        if codigo is None:
            break

        produto = buscar_por_codigo_barras(codigo)
        if produto is None:
            print("Produto não encontrado ou inativo.\n")

            resposta = input("Deseja cadastrar este produto? (S/N): ").strip().upper()

            if resposta == "S":
                executar_cadastro(codigo)

                produto = buscar_por_codigo_barras(codigo)

                if produto is None:
                    print("Falha ao cadastrar.")
                    continue
            else:
                continue

        nome_produto = produto[4]  # coluna nome_produto

        try:
            quantidade = int(input(f"Quantidade comprada de '{nome_produto}': "))
            valor_custo = float(input(f"Valor de custo (unitário) de '{nome_produto}': "))
            margem = float(input("Margem de lucro (ex: 0.3 para 30%): "))
        except ValueError:
            print("Valor inválido, tente novamente.\n")
            continue

        try:
            sub_total, preco_venda = adicionar_item_compra(id_compra, codigo, quantidade, valor_custo, margem)
            total_itens += 1
            print(
                f"Adicionado: {quantidade}x {nome_produto} "
                f"(custo total R$ {sub_total:.2f}, novo preço de venda R$ {preco_venda:.2f})\n"
            )
        except ValueError as e:
            print(f"Erro: {e}\n")

    if total_itens == 0:
        cancelar_compra(id_compra)
        print("Nenhum item adicionado. Compra cancelada.")
        sys.exit()

    total = calcular_total_compra(id_compra)
    print(f"\nTotal da compra (custo): R$ {total:.2f}")

    confirmar = input("Finalizar compra? (s/n): ").strip().lower()

    if confirmar != "s":
        cancelar_compra(id_compra)
        print("Compra cancelada. Estoque de depósito revertido.")
        sys.exit()

    try:
        total_final = finalizar_compra(id_compra)
        print(f"\nCompra {id_compra} finalizada com sucesso!")
        print(f"Total investido: R$ {total_final:.2f}")
    except ValueError as e:
        print(f"Erro ao finalizar compra: {e}")