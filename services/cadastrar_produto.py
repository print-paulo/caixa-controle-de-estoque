import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.leitor_barras import codigo_lido
from utils.conectar_banco import conectar_banco


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
    conn = conectar_banco()
    try:
        conn.execute(f"UPDATE produto SET {coluna} = ? WHERE id_produto = ?", (valor, id_produto))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao adicionar {coluna}: {e}")
    finally:
        conn.close()


def _atualizar_campo_estoque(id_produto, coluna, valor):
    """Função interna: faz o UPDATE de uma única coluna da tabela estoque."""
    conn = conectar_banco()
    try:
        conn.execute(
            f"UPDATE estoque SET {coluna} = ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id_produto = ?",
            (valor, id_produto),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao adicionar {coluna}: {e}")
    finally:
        conn.close()


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
    return _atualizar_campo_produto(id_produto, "codigo_barras", codigo_barras)


def adicionar_codigo_barras_com_leitor(id_produto):
    """Lê o código de barras direto do leitor, em vez de receber por parâmetro."""
    print("Aponte o leitor para o código de barras do produto (ou digite 'sair' para cancelar):")
    codigo = codigo_lido()
    if codigo is None:
        print("Operação cancelada.")
        return False
    return adicionar_codigo_barras(id_produto, codigo)


def adicionar_quantidade(id_produto, quantidade):
    if quantidade is not None and quantidade < 0:
        raise ValueError("Quantidade não pode ser negativa.")
    return _atualizar_campo_produto(id_produto, "quantidade", quantidade)


def adicionar_medida_quantidade(id_produto, medida_quantidade):
    return _atualizar_campo_produto(id_produto, "medida_quantidade", medida_quantidade)


def adicionar_unidade(id_produto, unidade):
    return _atualizar_campo_produto(id_produto, "unidade", unidade)


def adicionar_valor_unitario(id_produto, valor_unitario):
    if valor_unitario is None or valor_unitario < 0:
        raise ValueError("Valor unitário não pode ser negativo.")
    return _atualizar_campo_produto(id_produto, "valor_unitario", valor_unitario)


# ---------- campos da tabela estoque ----------

def adicionar_estoque_deposito(id_produto, valor):
    if valor is not None and valor < 0:
        raise ValueError("Estoque de depósito não pode ser negativo.")
    return _atualizar_campo_estoque(id_produto, "estoque_deposito", valor)


def adicionar_estoque_exposicao(id_produto, valor):
    if valor is not None and valor < 0:
        raise ValueError("Estoque de exposição não pode ser negativo.")
    return _atualizar_campo_estoque(id_produto, "estoque_exposicao", valor)


def adicionar_capacidade_exposicao(id_produto, valor):
    if valor is not None and valor < 0:
        raise ValueError("Capacidade de exposição não pode ser negativa.")
    return _atualizar_campo_estoque(id_produto, "capacidade_exposicao", valor)


def adicionar_estoque_minimo(id_produto, valor):
    if valor is not None and valor < 0:
        raise ValueError("Estoque mínimo não pode ser negativo.")
    return _atualizar_campo_estoque(id_produto, "estoque_minimo", valor)