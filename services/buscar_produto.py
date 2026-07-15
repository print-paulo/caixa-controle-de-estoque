import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco


def buscar_por_codigo_barras(codigo):
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT *
        FROM produto
        WHERE codigo_barras = ?
        AND ativo = 1
    """, (codigo,))

    produto = cursor.fetchone()
    conn.close()

    return produto

#Pra usar a função de busca, o codigo precisa ser algo como isso:
# codigo = codigo_lido()
# produto = buscar_por_codigo_barras(codigo)

def buscar_por_nome(nome):
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT *
        FROM produto
        WHERE nome_produto LIKE ?
        AND ativo = 1
    """, (f"%{nome}%",))

    produtos = cursor.fetchall()
    conn.close()

    return produtos

def buscar_por_id(id_produto):
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT *
        FROM produto
        WHERE id_produto = ?
        AND ativo = 1
    """, (id_produto,))

    produto = cursor.fetchone()
    conn.close()

    return produto

def _buscar_campo_por_id(id_produto, coluna):
    """Função interna: busca o valor de uma única coluna da tabela produto pelo id."""
    conn = conectar_banco()
    cursor = conn.execute(f"SELECT {coluna} FROM produto WHERE id_produto = ?", (id_produto,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None


def buscar_nome_por_id(id_produto):
    return _buscar_campo_por_id(id_produto, "nome_produto")

def buscar_categoria_por_id(id_produto):
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT c.nome_categoria
        FROM produto p
        LEFT JOIN categoria c ON p.id_categoria = c.id_categoria
        WHERE p.id_produto = ?
    """, (id_produto,))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None

def buscar_codigo_barras_por_id(id_produto):
    return _buscar_campo_por_id(id_produto, "codigo_barras")

def buscar_medida_quantidade_por_id(id_produto):
    return _buscar_campo_por_id(id_produto, "medida_quantidade")

def buscar_unidade_por_id(id_produto):
    return _buscar_campo_por_id(id_produto, "unidade")

def buscar_valor_unitario_por_id(id_produto):
    return _buscar_campo_por_id(id_produto, "valor_unitario")

def listar_todos():
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT *
        FROM produto
        WHERE ativo = 1
        ORDER BY nome_produto
    """)

    produtos = cursor.fetchall()
    conn.close()

    return produtos

#pra chamar o listar_todos seria algo como isso:
# produtos = listar_todos()
# for produto in produtos:
#    print(produto)