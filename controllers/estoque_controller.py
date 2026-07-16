import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.estoque import (
    consultar_estoque_por_id,
    listar_estoque_completo,
    listar_produtos_abaixo_minimo,
    repor_exposicao,
    ajustar_estoque_deposito,
    ajustar_estoque_exposicao,
    listar_movimentos,
)
from services.buscar_produto import buscar_por_codigo_barras
from utils.leitor_barras import codigo_lido


def _obter_id_produto():
    """
    Pergunta se o usuário quer informar o id direto ou passar o produto
    no leitor, e devolve o id_produto (ou None se cancelado/inválido).
    """
    print("1 - Informar id do produto")
    print("2 - Passar código de barras")
    opcao = input("Escolha: ")

    if opcao == "1":
        try:
            return int(input("Id do produto: "))
        except ValueError:
            print("Id inválido.")
            return None

    elif opcao == "2":
        codigo = codigo_lido()
        if codigo is None:
            return None
        produto = buscar_por_codigo_barras(codigo)
        if produto is None:
            print("Produto não encontrado ou inativo.")
            return None
        return produto[0]  # id_produto

    print("Opção inválida.")
    return None


# ----------- consultar --------------

def executar_consulta():
    print("\n1 - Consultar um produto")
    print("2 - Listar estoque completo")
    opcao = input("Escolha: ")

    if opcao == "1":
        id_produto = _obter_id_produto()
        if id_produto is None:
            return
        estoque = consultar_estoque_por_id(id_produto)
        if estoque is None:
            print("Estoque não encontrado para esse produto.")
            return
        _imprimir_linha_estoque(estoque)

    elif opcao == "2":
        linhas = listar_estoque_completo()
        if not linhas:
            print("Nenhum produto cadastrado.")
        for linha in linhas:
            _imprimir_linha_estoque(linha)

    else:
        print("Opção inválida.")


def _imprimir_linha_estoque(linha):
    id_produto, nome, deposito, exposicao, capacidade, minimo, atualizado = linha
    print(
        f"[{id_produto}] {nome} — depósito: {deposito} | exposição: {exposicao} "
        f"| capacidade exposição: {capacidade} | mínimo: {minimo} | atualizado em: {atualizado}"
    )


# ----------- abaixo do mínimo --------------

def executar_produtos_abaixo_minimo():
    produtos = listar_produtos_abaixo_minimo()
    if not produtos:
        print("Nenhum produto abaixo do estoque mínimo.")
        return

    print("\nProdutos no mínimo ou abaixo dele (depósito):")
    for id_produto, nome, deposito, exposicao, minimo in produtos:
        print(f"[{id_produto}] {nome} — depósito: {deposito} | exposição: {exposicao} | mínimo: {minimo}")


# ----------- repor exposição --------------

def executar_reposicao():
    id_produto = _obter_id_produto()
    if id_produto is None:
        return

    quantidade_str = input("Quantidade a repor (Enter para repor automaticamente até a capacidade): ").strip()

    try:
        quantidade = None if quantidade_str == "" else int(quantidade_str)
        movido = repor_exposicao(id_produto, quantidade)

        if movido == 0:
            print("Nada foi movido (exposição já está na capacidade, ou depósito está vazio).")
        else:
            print(f"{movido} unidade(s) movida(s) do depósito para a exposição.")

    except ValueError as e:
        print(f"Erro: {e}")


# ----------- ajustar estoque --------------

def executar_ajuste():
    """
    Ajuste manual de estoque (achou mais, quebrou, perdeu, contagem
    física divergente etc.). Diferente da edição de produto: aqui você
    informa quanto SOMAR ou SUBTRAIR, não o valor final.
    """
    id_produto = _obter_id_produto()
    if id_produto is None:
        return

    print("\n1 - Ajustar estoque de depósito")
    print("2 - Ajustar estoque de exposição")
    opcao = input("Escolha: ")

    if opcao not in ("1", "2"):
        print("Opção inválida.")
        return

    try:
        delta = int(input("Quantidade a ajustar (positivo pra somar, negativo pra subtrair): "))
    except ValueError:
        print("Valor inválido.")
        return

    try:
        if opcao == "1":
            novo_valor = ajustar_estoque_deposito(id_produto, delta)
            print(f"Estoque de depósito ajustado. Novo valor: {novo_valor}")
        else:
            novo_valor = ajustar_estoque_exposicao(id_produto, delta)
            print(f"Estoque de exposição ajustado. Novo valor: {novo_valor}")

    except ValueError as e:
        print(f"Erro: {e}")


# ----------- histórico --------------

_TIPOS_MOVIMENTO = {
    "1": "VENDA",
    "2": "CANCELAMENTO_VENDA",
    "3": "COMPRA",
    "4": "CANCELAMENTO_COMPRA",
    "5": "REPOSICAO",
    "6": "REPOSICAO_MANUAL",
    "7": "AJUSTE",
}


def executar_historico():
    print("\n1 - Histórico de um produto específico")
    print("2 - Histórico geral (todos os produtos)")
    opcao = input("Escolha: ")

    id_produto = None
    if opcao == "1":
        id_produto = _obter_id_produto()
        if id_produto is None:
            return
    elif opcao != "2":
        print("Opção inválida.")
        return

    print("\nFiltrar por tipo de movimento? (Enter pra não filtrar)")
    print("1-VENDA 2-CANCELAMENTO_VENDA 3-COMPRA 4-CANCELAMENTO_COMPRA 5-REPOSICAO 6-REPOSICAO_MANUAL 7-AJUSTE")
    escolha_tipo = input("Escolha: ").strip()
    tipo = _TIPOS_MOVIMENTO.get(escolha_tipo)

    movimentos = listar_movimentos(id_produto=id_produto, tipo=tipo)

    if not movimentos:
        print("Nenhuma movimentação encontrada.")
        return

    print()
    for id_mov, id_prod, nome, tipo_mov, campo, quantidade, origem_id, data_hora in movimentos:
        sinal = "+" if quantidade >= 0 else ""
        origem = f" (origem: {origem_id})" if origem_id is not None else ""
        print(f"[{data_hora}] {nome} — {tipo_mov} em {campo}: {sinal}{quantidade}{origem}")