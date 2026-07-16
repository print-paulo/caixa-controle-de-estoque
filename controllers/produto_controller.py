import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.cadastrar_produto import (
    adicionar_categoria,
    input_codigo_barras_produto,
    adicionar_medida_quantidade,
    adicionar_unidade,
    adicionar_capacidade_exposicao,
    adicionar_estoque_minimo,
    input_campo_produto,
    input_cadastro_nome_produto,
)
from services.editar_produto import (
    editar_nome_produto,
    editar_categoria,
    editar_codigo_barras,
    editar_medida_quantidade,
    editar_unidade,
    editar_valor_unitario,
    editar_estoque_deposito,
    editar_estoque_exposicao,
)
from services.excluir_produto import excluir_produto_permanente, excluir_produto, reativar_produto
from services.buscar_produto import (
    buscar_por_codigo_barras,
    buscar_por_nome,
    buscar_por_id,
    listar_todos,
)
from utils.leitor_barras import codigo_lido


# ----------- cadastro --------------

def executar_cadastro(codigo_barras=None):
    """
    Fluxo completo de cadastro de um novo produto.
    Se `codigo_barras` for informado (ex: já lido durante uma compra),
    tenta usar esse valor antes de pedir a leitura manual.
    Retorna o id_produto criado, ou None se o cadastro for cancelado
    na etapa do código de barras.
    """
    while True:
        try:
            id_produto = input_cadastro_nome_produto()

            input_campo_produto("Digite a categoria do produto: ", adicionar_categoria, id_produto)

            if not input_codigo_barras_produto(id_produto, codigo_barras):
                excluir_produto_permanente(id_produto)
                return None

            input_campo_produto("Digite a medida da quantidade: ", adicionar_medida_quantidade, id_produto)
            input_campo_produto("Digite a unidade do produto: ", adicionar_unidade, id_produto)
            input_campo_produto("Digite a capacidade minima de exposição: ", adicionar_capacidade_exposicao, id_produto, int)
            input_campo_produto("Informe a quantidade minima para se ter em estoque: ", adicionar_estoque_minimo, id_produto, int)

            print(f"\nProduto cadastrado com sucesso (id {id_produto}).")
            return id_produto

        except ValueError as e:
            print(f"\nErro: {e}")
            # Remove o cadastro incompleto
            if "id_produto" in locals():
                excluir_produto_permanente(id_produto)
                del id_produto


# ----------- edição --------------

def executar_edicao():
    """
    Fluxo de edição de um produto existente. Deixar o campo em branco
    mantém o valor atual (comportamento já garantido pelos services de
    edição, exceto para estoque_deposito/estoque_exposicao — ver aviso).
    """
    try:
        id_produto = int(input("Id do produto a editar: "))
    except ValueError:
        print("Id inválido.")
        return

    produto = buscar_por_id(id_produto)
    if produto is None:
        print("Produto não encontrado.")
        return

    print(f"Produto atual: {produto}")

    try:
        editar_nome_produto(id_produto, input("Novo nome (Enter para manter): ").strip().upper())
        editar_categoria(id_produto, input("Nova categoria (Enter para manter): ").strip().upper())
        editar_codigo_barras(id_produto, input("Novo código de barras (Enter para manter): ").strip())
        editar_medida_quantidade(id_produto, input("Nova medida, ex: 750ML (Enter para manter): ").strip().upper())
        editar_unidade(id_produto, input("Nova unidade (Enter para manter): ").strip().upper())

        novo_valor_unitario = input("Novo valor unitário (Enter para manter): ").strip()
        novo_valor_unitario = None if novo_valor_unitario == "" else float(novo_valor_unitario)
        editar_valor_unitario(id_produto, novo_valor_unitario)

        # ATENÇÃO: diferente dos campos acima, estas duas funções não têm
        # tratamento de "branco = manter valor atual" — um Enter aqui
        # gravaria 0/None de verdade. Por isso aqui só chamamos se algo
        # for digitado.
        novo_estoque_deposito = input("Novo estoque de depósito (Enter para pular esta edição): ").strip()
        if novo_estoque_deposito != "":
            editar_estoque_deposito(id_produto, int(novo_estoque_deposito))

        novo_estoque_exposicao = input("Novo estoque de exposição (Enter para pular esta edição): ").strip()
        if novo_estoque_exposicao != "":
            editar_estoque_exposicao(id_produto, int(novo_estoque_exposicao))

        print("\nProduto atualizado com sucesso.")

    except ValueError as e:
        print(f"\nErro: {e}")


# ----------- exclusão --------------

def executar_exclusao():
    try:
        id_produto = int(input("Id do produto a desativar: "))
    except ValueError:
        print("Id inválido.")
        return

    if excluir_produto(id_produto):
        print("Produto desativado com sucesso.")
    else:
        print("Produto não encontrado ou já estava desativado.")


def executar_reativacao():
    try:
        id_produto = int(input("Id do produto a reativar: "))
    except ValueError:
        print("Id inválido.")
        return

    if reativar_produto(id_produto):
        print("Produto reativado com sucesso.")
    else:
        print("Produto não encontrado ou já está ativo.")


# ----------- busca --------------

def executar_busca():
    print("\n1 - Por código de barras")
    print("2 - Por nome")
    print("3 - Listar todos")
    opcao = input("Escolha: ")

    if opcao == "1":
        print("Passe o produto (ou digite 'sair' para cancelar):")
        codigo = codigo_lido()
        if codigo is None:
            return
        produto = buscar_por_codigo_barras(codigo)
        print(produto if produto else "Produto não encontrado.")

    elif opcao == "2":
        nome = input("Nome (ou parte dele): ")
        produtos = buscar_por_nome(nome)
        if not produtos:
            print("Nenhum produto encontrado.")
        for produto in produtos:
            print(produto)

    elif opcao == "3":
        produtos = listar_todos()
        if not produtos:
            print("Nenhum produto cadastrado.")
        for produto in produtos:
            print(produto)

    else:
        print("Opção inválida.")