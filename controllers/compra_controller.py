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
from services.buscar_compra import (
    buscar_compra_por_id,
    listar_itens_compra,
    listar_compras,
    listar_compras_por_produto,
)
from controllers.produto_controller import executar_cadastro


def _pedir_custo_unitario(nome_produto):
    """
    Pergunta o custo unitário de duas formas possíveis:
    1 - direto, quando já se sabe quanto custa cada unidade
    2 - a partir do preço pago por caixa/pacote e quantas unidades vêm
        nela (o sistema calcula: preço da caixa / unidades na caixa)

    Levanta ValueError se a entrada for inválida (mesmo comportamento de
    antes, pra manter compatível com quem chama).
    """
    print(f"Custo de '{nome_produto}':")
    print("1 - Informar o valor por unidade direto")
    print("2 - Calcular a partir do preço da caixa/pacote")
    opcao = input("Escolha: ").strip()

    if opcao == "2":
        preco_caixa = float(input("Preço pago pela caixa/pacote: "))
        unidades_na_caixa = int(input("Quantas unidades vêm na caixa/pacote: "))
        if unidades_na_caixa <= 0:
            raise ValueError("Quantidade de unidades na caixa deve ser maior que zero.")
        custo_unitario = preco_caixa / unidades_na_caixa
        print(f"Custo por unidade calculado: R$ {custo_unitario:.4f}")
        return custo_unitario

    return float(input(f"Valor de custo (unitário) de '{nome_produto}': "))


def executar_compra():
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

        nome_produto = produto.nome_produto

        try:
            quantidade = int(input(f"Quantidade comprada de '{nome_produto}': "))
            valor_custo = _pedir_custo_unitario(nome_produto)
            margem = float(input("Margem de lucro (ex: 0.3 para 30%): "))
        except ValueError:
            print("Valor inválido, tente novamente.\n")
            continue

        try:
            sub_total, preco_venda = adicionar_item_compra(id_compra, codigo, quantidade, valor_custo, margem)
            total_itens += 1
            lucro_por_unidade = preco_venda - valor_custo
            print(
                f"Adicionado: {quantidade}x {nome_produto} "
                f"(custo total R$ {sub_total:.2f}, novo preço de venda R$ {preco_venda:.2f}, "
                f"lucro/unidade R$ {lucro_por_unidade:.2f})\n"
            )
        except ValueError as e:
            print(f"Erro: {e}\n")

    if total_itens == 0:
        cancelar_compra(id_compra)
        print("Nenhum item adicionado. Compra cancelada.")
        return

    total = calcular_total_compra(id_compra)
    print(f"\nTotal da compra (custo): R$ {total:.2f}")

    confirmar = input("Finalizar compra? (s/n): ").strip().lower()

    if confirmar != "s":
        cancelar_compra(id_compra)
        print("Compra cancelada. Estoque de depósito revertido.")
        return

    try:
        total_final = finalizar_compra(id_compra)
        print(f"\nCompra {id_compra} finalizada com sucesso!")
        print(f"Total investido: R$ {total_final:.2f}")
    except ValueError as e:
        print(f"Erro ao finalizar compra: {e}")


def executar_busca_compra():
    print("\n1 - Buscar compra por id")
    print("2 - Listar todas as compras")
    print("3 - Listar compras por status")
    print("4 - Histórico de compras de um produto")
    opcao = input("Escolha: ")

    if opcao == "1":
        try:
            id_compra = int(input("Id da compra: "))
        except ValueError:
            print("Id inválido.")
            return

        compra = buscar_compra_por_id(id_compra)
        if compra is None:
            print("Compra não encontrada.")
        else:
            _imprimir_compra(compra)
            print("\nItens da compra:")
            for item in listar_itens_compra(id_compra):
                _imprimir_item_compra(item)

    elif opcao == "2":
        for compra in listar_compras():
            _imprimir_compra(compra)

    elif opcao == "3":
        status = input("Status (ABERTA/FINALIZADA/CANCELADA): ").strip().upper()
        for compra in listar_compras(status=status):
            _imprimir_compra(compra)

    elif opcao == "4":
        try:
            id_produto = int(input("Id do produto: "))
        except ValueError:
            print("Id inválido.")
            return
        for registro in listar_compras_por_produto(id_produto):
            _imprimir_item_historico_compra(registro)

    else:
        print("Opção inválida.")


def _imprimir_compra(compra):
    print(
        f"[{compra.id_compra}] {compra.data_hora} | "
        f"fornecedor: {compra.fornecedor} | status: {compra.status}"
    )


def _imprimir_item_compra(item):
    lucro_por_unidade = item.valor_venda_calculado - item.valor_custo_unitario
    lucro_total = lucro_por_unidade * item.quantidade
    print(
        f"  {item.nome_produto} — {item.quantidade}x "
        f"custo R$ {item.valor_custo_unitario:.2f} = R$ {item.sub_total:.2f} "
        f"(preço de venda: R$ {item.valor_venda_calculado:.2f} | "
        f"lucro/unidade: R$ {lucro_por_unidade:.2f} | lucro total esperado: R$ {lucro_total:.2f})"
    )


def _imprimir_item_historico_compra(registro):
    print(
        f"[compra {registro['id_compra']}] {registro['data_hora']} — "
        f"{registro['quantidade']}x custo R$ {registro['valor_custo_unitario']:.2f} = R$ {registro['sub_total']:.2f}"
    )