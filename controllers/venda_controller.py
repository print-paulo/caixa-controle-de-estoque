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
    eh_pagamento_no_cartao,
    TAXA_CARTAO,
)
from services.buscar_venda import (
    buscar_venda_por_id,
    listar_itens_venda,
    listar_vendas,
    listar_vendas_por_produto,
)


def executar_venda():
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

        nome_produto = produto.nome_produto

        try:
            quantidade = int(input(f"Quantidade de '{nome_produto}': "))
        except ValueError:
            print("Quantidade inválida, tente novamente.\n")
            continue

        try:
            resultado = adicionar_item_venda(id_venda, codigo, quantidade)

            sub_total = resultado["subtotal"]
            estoque_baixo = resultado["estoque_baixo"]
            quantidade_reposta = resultado["quantidade_reposta"]

            total_itens += 1
            print(f"Adicionado: {quantidade}x {nome_produto} = R$ {sub_total:.2f}\n")

            if quantidade_reposta:
                print(f"Reposição automática: {quantidade_reposta} unidades.")

            if estoque_baixo:
                print(f"Atenção: o produto '{nome_produto}' está abaixo do estoque mínimo.")

        except ValueError as e:
            print(f"Erro: {e}\n")

    if total_itens == 0:
        cancelar_venda(id_venda)
        print("Nenhum item adicionado. Venda cancelada.")
        return

    total = calcular_total_venda(id_venda)
    print(f"\nTotal da venda: R$ {total:.2f}")

    confirmar = input("Finalizar venda? (s/n): ").strip().lower()

    if confirmar != "s":
        cancelar_venda(id_venda)
        print("Venda cancelada. Estoque devolvido.")
        return

    forma_pagamento = input("Forma de pagamento (dinheiro/cartao/pix): ").strip().lower()

    try:
        total_final = finalizar_venda(id_venda, forma_pagamento)
        print(f"\nVenda {id_venda} finalizada com sucesso!")
        print(f"Forma de pagamento: {forma_pagamento}")
        if eh_pagamento_no_cartao(forma_pagamento):
            print(f"(Taxa de cartão de {TAXA_CARTAO * 100:.0f}% aplicada sobre o subtotal de R$ {total:.2f})")
        print(f"Total: R$ {total_final:.2f}")
    except ValueError as e:
        print(f"Erro ao finalizar venda: {e}")


def executar_busca_venda():
    print("\n1 - Buscar venda por id")
    print("2 - Listar todas as vendas")
    print("3 - Listar vendas por status")
    print("4 - Histórico de vendas de um produto")
    opcao = input("Escolha: ")

    if opcao == "1":
        try:
            id_venda = int(input("Id da venda: "))
        except ValueError:
            print("Id inválido.")
            return

        venda = buscar_venda_por_id(id_venda)
        if venda is None:
            print("Venda não encontrada.")
        else:
            _imprimir_venda(venda)
            print("\nItens da venda:")
            for item in listar_itens_venda(id_venda):
                _imprimir_item_venda(item)

    elif opcao == "2":
        for venda in listar_vendas():
            _imprimir_venda(venda)

    elif opcao == "3":
        status = input("Status (ABERTA/FINALIZADA/CANCELADA): ").strip().upper()
        for venda in listar_vendas(status=status):
            _imprimir_venda(venda)

    elif opcao == "4":
        try:
            id_produto = int(input("Id do produto: "))
        except ValueError:
            print("Id inválido.")
            return
        for registro in listar_vendas_por_produto(id_produto):
            _imprimir_item_historico_venda(registro)

    else:
        print("Opção inválida.")


def _imprimir_venda(venda):
    valor = f"R$ {venda.valor_total:.2f}" if venda.valor_total is not None else "—"
    print(
        f"[{venda.id_venda}] {venda.data_hora} | "
        f"pagamento: {venda.forma_pagamento} | total: {valor} | status: {venda.status}"
    )


def _imprimir_item_venda(item):
    print(
        f"  {item.nome_produto} — {item.quantidade}x "
        f"R$ {item.valor_unitario_momento:.2f} = R$ {item.sub_total:.2f}"
    )


def _imprimir_item_historico_venda(registro):
    print(
        f"[venda {registro['id_venda']}] {registro['data_hora']} — "
        f"{registro['quantidade']}x R$ {registro['valor_unitario_momento']:.2f} = R$ {registro['sub_total']:.2f}"
    )