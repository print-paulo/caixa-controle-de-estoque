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
    ajustar_capacidade_exposicao,
    ajustar_estoque_minimo,
    listar_movimentos,
)
from services.buscar_produto import (
    buscar_por_codigo_barras,
    buscar_estoque_deposito_por_id,
    buscar_estoque_exposicao_por_id,
    buscar_capacidade_exposicao_por_id,
    buscar_estoque_minimo_por_id,
)
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
        return produto.id_produto

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


def _imprimir_linha_estoque(estoque):
    print(
        f"[{estoque.id_produto}] {estoque.nome_produto} — depósito: {estoque.estoque_deposito} "
        f"| exposição: {estoque.estoque_exposicao} | capacidade exposição: {estoque.capacidade_exposicao} "
        f"| mínimo: {estoque.estoque_minimo} | atualizado em: {estoque.ultima_atualizacao}"
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

_CAMPOS_AJUSTAVEIS = {
    "1": ("estoque de depósito", ajustar_estoque_deposito, buscar_estoque_deposito_por_id),
    "2": ("estoque de exposição", ajustar_estoque_exposicao, buscar_estoque_exposicao_por_id),
    "3": ("estoque mínimo", ajustar_estoque_minimo, buscar_estoque_minimo_por_id),
    "4": ("capacidade de exposição", ajustar_capacidade_exposicao, buscar_capacidade_exposicao_por_id),
}


def executar_ajuste():
    """
    Ajusta um dos campos numéricos de estoque (depósito, exposição,
    estoque mínimo ou capacidade de exposição) pro valor que o usuário
    quer ver -- sem precisar calcular soma/subtração de cabeça.

    Por trás dos panos, o sistema mostra o valor atual, pede o valor
    final desejado, calcula o delta necessário (novo - atual) e usa a
    mesma função de ajuste por delta (com validação de não ficar
    negativo e log no histórico de movimentação) usada em todo o resto
    do sistema.
    """
    id_produto = _obter_id_produto()
    if id_produto is None:
        return

    print("\n1 - Ajustar estoque de depósito")
    print("2 - Ajustar estoque de exposição")
    print("3 - Ajustar estoque mínimo")
    print("4 - Ajustar capacidade de exposição")
    opcao = input("Escolha: ")

    if opcao not in _CAMPOS_AJUSTAVEIS:
        print("Opção inválida.")
        return

    nome_campo, funcao_ajuste, funcao_buscar_atual = _CAMPOS_AJUSTAVEIS[opcao]

    valor_atual = funcao_buscar_atual(id_produto)
    if valor_atual is None:
        print(f"Não foi possível encontrar o valor atual de {nome_campo} para esse produto.")
        return

    print(f"Valor atual de {nome_campo}: {valor_atual}")

    try:
        novo_valor_desejado = int(input(f"Novo valor de {nome_campo}: "))
    except ValueError:
        print("Valor inválido.")
        return

    delta = novo_valor_desejado - valor_atual

    try:
        novo_valor = funcao_ajuste(id_produto, delta)
        print(f"{nome_campo.capitalize()} ajustado. Novo valor: {novo_valor}")
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
    for mov in movimentos:
        sinal = "+" if mov.quantidade >= 0 else ""
        origem = f" (origem: {mov.origem_id})" if mov.origem_id is not None else ""
        print(f"[{mov.data_hora}] {mov.nome_produto} — {mov.tipo} em {mov.campo}: {sinal}{mov.quantidade}{origem}")