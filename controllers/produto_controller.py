import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.cadastrar_produto import cadastrar_produto_completo
from services.editar_produto import (
    editar_nome_produto,
    editar_categoria,
    editar_codigo_barras,
    editar_medida_embalagem,
    editar_unidade,
    editar_valor_unitario,
    editar_estoque_deposito,
    editar_estoque_exposicao,
)

from services.excluir_produto import excluir_produto, reativar_produto

from services.buscar_produto import (
    buscar_por_codigo_barras,
    buscar_por_nome,
    listar_todos, buscar_nome_por_id,
)
from utils.leitor_barras import codigo_lido

# ----------- inputs --------------

def _pedir_texto(prompt, obrigatorio=True):
    """Pede um texto ao usuário. Não toca no banco -- só coleta e valida formato."""
    while True:
        valor = input(prompt).strip().upper()
        if valor or not obrigatorio:
            return valor or None
        print("Valor não pode ser vazio.")


def _pedir_inteiro_nao_negativo(prompt):
    """Pede um inteiro >= 0 ao usuário. Não toca no banco."""
    while True:
        valor = input(prompt).strip()
        try:
            valor_convertido = int(valor)
        except ValueError:
            print("Valor inválido, digite um número inteiro.")
            continue
        if valor_convertido < 0:
            print("Valor não pode ser negativo.")
            continue
        return valor_convertido


def _pedir_codigo_barras(codigo_barras=None):
    """
    Resolve o código de barras a usar no cadastro. Se `codigo_barras` já
    foi informado (ex: lido durante uma compra), usa ele direto. Senão,
    pede pro usuário passar no leitor. Retorna None se cancelado.
    """
    if codigo_barras is not None:
        return codigo_barras

    print("Aponte o leitor para o código de barras do produto (ou digite 'sair' para cancelar):")
    return codigo_lido()


def input_campo_editar(prompt, func_editar, id_produto, tipo_dado=str):
    """
    Pede um valor pro usuário editar um campo. Deixar em branco (só Enter)
    mantém o valor atual -- a própria função editar_* sabe fazer isso ao
    receber None. Se o tipo não for válido, ou a validação (ex: negativo)
    falhar, pede de novo só esse campo -- não reinicia a edição inteira.
    """
    while True:
        valor = input(prompt).strip().upper()
        if not valor:
            return func_editar(id_produto, None)
        try:
            valor_convertido = tipo_dado(valor)
        except (TypeError, ValueError):
            print("Valor inválido para este campo. Tente novamente.")
            continue
        try:
            return func_editar(id_produto, valor_convertido)
        except ValueError as e:
            print(f"Erro: {e}")

# ----------- cadastro --------------

def executar_cadastro(codigo_barras=None):
    """
    Fluxo completo de cadastro de um novo produto.

    Todos os dados são coletados primeiro (nome, categoria, medida,
    unidade, capacidade, mínimo) -- essa etapa é só input em memória,
    nada é gravado no banco ainda. Só o código de barras e a gravação
    final tocam no banco, e como `cadastrar_produto_completo` grava tudo
    numa única transação, não existe mais "produto pela metade": se o
    programa for interrompido a qualquer momento (Ctrl+C, terminal
    fechado, queda de energia), ou o cadastro foi salvo por completo,
    ou não foi salvo nada.

    Se `codigo_barras` for informado (ex: já lido durante uma compra),
    tenta usar esse valor antes de pedir a leitura manual.
    Retorna o id_produto criado, ou None se o cadastro for cancelado
    na etapa do código de barras.
    """
    nome = _pedir_texto("Digite o nome do produto: ")
    categoria = _pedir_texto("Digite a categoria do produto: ", obrigatorio=False)
    medida_embalagem = _pedir_texto("Digite a medida da embalagem: ", obrigatorio=False)
    unidade = _pedir_texto("Digite a unidade do produto: ", obrigatorio=False)
    capacidade = _pedir_inteiro_nao_negativo("Digite a capacidade minima de exposição: ")
    minimo = _pedir_inteiro_nao_negativo("Informe a quantidade minima para se ter em estoque: ")

    codigo = codigo_barras
    while True:
        codigo = _pedir_codigo_barras(codigo)
        if codigo is None:
            print("Operação cancelada.")
            return None

        try:
            id_produto = cadastrar_produto_completo(
                nome_produto=nome,
                nome_categoria=categoria,
                codigo_barras=codigo,
                medida_embalagem=medida_embalagem,
                unidade=unidade,
                capacidade_exposicao=capacidade,
                estoque_minimo=minimo,
            )
            print(f"\nProduto cadastrado com sucesso (id {id_produto}).")
            return id_produto

        except ValueError as e:
            print(f"\nErro: {e}")
            codigo = None  # o único erro possível aqui é código duplicado; pede um novo




# ----------- edição --------------

def executar_edicao():
    try:
        id_produto = int(input("Id do produto a editar: "))
    except ValueError:
        print("Id inválido.")
        return None

    nome_atual = buscar_nome_por_id(id_produto)
    if nome_atual is None:
        print(f"Produto com id {id_produto} não encontrado.")
        return None

    print(f"Produto atual: {nome_atual}")
    print("(Deixe em branco e aperte Enter pra manter o valor atual em qualquer campo)\n")

    input_campo_editar("Novo nome do produto: ", editar_nome_produto, id_produto)
    input_campo_editar("Nova categoria: ", editar_categoria, id_produto)
    input_campo_editar("Novo código de barras: ", editar_codigo_barras, id_produto)
    input_campo_editar("Nova quantidade (ex: 750ML, 1L): ", editar_quantidade, id_produto)
    input_campo_editar("Nova unidade: ", editar_unidade, id_produto)
    input_campo_editar("Novo valor unitário: ", editar_valor_unitario, id_produto, float)
    input_campo_editar("Novo estoque de depósito: ", editar_estoque_deposito, id_produto, int)
    input_campo_editar("Novo estoque de exposição: ", editar_estoque_exposicao, id_produto, int)

    print(f"\nProduto (id {id_produto}) atualizado com sucesso.")
    return id_produto

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