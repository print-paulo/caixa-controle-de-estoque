import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.excluir_produto import excluir_produto_permanente
from utils.leitor_barras import codigo_lido
from utils.conectar_banco import conectar_banco
from utils.validacoes import validar_nao_negativo
from utils.db_campos import atualizar_campo_produto, atualizar_campo_estoque
from services.buscar_produto import buscar_por_codigo_barras

def obter_ou_criar_categoria(conn, nome_categoria):
    """Busca o id da categoria pelo nome; cria se não existir."""
    if not nome_categoria or not nome_categoria.strip():
        return None

    nome_categoria = nome_categoria.strip()
    cursor = conn.execute(
        "SELECT id_categoria FROM categoria WHERE nome_categoria = ?", (nome_categoria,)
    )
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]

    cursor = conn.execute(
        "INSERT INTO categoria (nome_categoria) VALUES (?)", (nome_categoria,)
    )
    return cursor.lastrowid


def _atualizar_campo_produto(id_produto, coluna, valor):
    """Função interna: faz o UPDATE de uma única coluna da tabela produto."""
    return atualizar_campo_produto(id_produto, coluna, valor, contexto="adicionar")


def _atualizar_campo_estoque(id_produto, coluna, valor):
    """Função interna: faz o UPDATE de uma única coluna da tabela estoque."""
    return atualizar_campo_estoque(id_produto, coluna, valor, contexto="adicionar")


def cadastrar_produto_base(nome_produto):
    """
    Cria o produto só com o nome (obrigatório) e a linha de estoque zerada.
    Os outros campos ficam NULL/0 até serem preenchidos pelas funções
    adicionar_* abaixo. Retorna o id_produto criado.
    """
    if not nome_produto or not nome_produto.strip():
        raise ValueError("Nome do produto não pode ser vazio.")

    conn = conectar_banco()
    try:
        cursor = conn.execute(
            "INSERT INTO produto (nome_produto) VALUES (?)", (nome_produto.strip(),)
        )
        id_produto = cursor.lastrowid

        conn.execute("""
            INSERT INTO estoque
            (id_produto, estoque_deposito, estoque_exposicao, capacidade_exposicao, estoque_minimo, ultima_atualizacao)
            VALUES (?, 0, 0, NULL, 0, CURRENT_TIMESTAMP)
        """, (id_produto,))

        conn.commit()
        return id_produto
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao cadastrar produto: {e}")
    finally:
        conn.close()


# ---------- campos da tabela produto ----------

def adicionar_categoria(id_produto, nome_categoria):
    conn = conectar_banco()
    try:
        id_categoria = obter_ou_criar_categoria(conn, nome_categoria)
        conn.execute("UPDATE produto SET id_categoria = ? WHERE id_produto = ?", (id_categoria, id_produto))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao adicionar categoria: {e}")
    finally:
        conn.close()


def adicionar_codigo_barras(id_produto, codigo_barras):
    produto = buscar_por_codigo_barras(codigo_barras)
    if produto is not None:
        raise ValueError(
            f"O código de barras '{codigo_barras}' já está cadastrado."
        )
    return _atualizar_campo_produto(
        id_produto,
        "codigo_barras",
        codigo_barras
    )


def input_codigo_barras_produto(id_produto, codigo_barras=None):
    """
    Cadastra o código de barras do produto.

    Se `codigo_barras` for informado (ex: já lido durante uma compra),
    tenta usar esse valor direto, sem pedir nova leitura. Se ele já
    estiver em uso, cai pro fluxo de leitura manual abaixo.

    Em qualquer caso de código duplicado, só pede um novo código de
    barras — não reinicia o resto do cadastro (nome, categoria, etc).

    Retorna False se o usuário cancelar a leitura (digitando 'sair').
    """
    if codigo_barras is not None:
        try:
            adicionar_codigo_barras(id_produto, codigo_barras)
            return True
        except ValueError as e:
            print(f"Erro: {e}")

    print("Aponte o leitor para o código de barras do produto (ou digite 'sair' para cancelar):")
    while True:
        codigo = codigo_lido()
        if codigo is None:
            print("Operação cancelada.")
            return False
        try:
            adicionar_codigo_barras(id_produto, codigo)
            return True
        except ValueError as e:
            print(f"Erro: {e}")


def adicionar_medida_quantidade(id_produto, medida_quantidade):
    return _atualizar_campo_produto(id_produto, "medida_quantidade", medida_quantidade)


def adicionar_unidade(id_produto, unidade):
    return _atualizar_campo_produto(id_produto, "unidade", unidade)


def adicionar_valor_unitario(id_produto, valor_unitario):
    validar_nao_negativo(valor_unitario, "Valor unitário", permitir_none=False)
    return _atualizar_campo_produto(id_produto, "valor_unitario", valor_unitario)


# ---------- campos da tabela estoque ----------

def adicionar_estoque_deposito(id_produto, valor):
    validar_nao_negativo(valor, "Estoque de depósito")
    return _atualizar_campo_estoque(id_produto, "estoque_deposito", valor)


def adicionar_estoque_exposicao(id_produto, valor):
    validar_nao_negativo(valor, "Estoque de exposição")
    return _atualizar_campo_estoque(id_produto, "estoque_exposicao", valor)


def adicionar_capacidade_exposicao(id_produto, valor):
    validar_nao_negativo(valor, "Capacidade de exposição", feminino=True)
    return _atualizar_campo_estoque(id_produto, "capacidade_exposicao", valor)


def adicionar_estoque_minimo(id_produto, valor):
    validar_nao_negativo(valor, "Estoque mínimo")
    return _atualizar_campo_estoque(id_produto, "estoque_minimo", valor)
