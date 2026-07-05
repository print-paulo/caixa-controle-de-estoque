import sqlite3
from pathlib import Path

PASTA_SCRIPT = Path(__file__).resolve().parent
BANCO = PASTA_SCRIPT.parent / "database" / "banco.db"

def conectar():
    return sqlite3.connect(BANCO)

def buscar_por_codigo_barras(codigo):
    conn = conectar()
    cursor = conn.execute("""
        SELECT *
        FROM produto
        WHERE codigo_barras = ?
    """, (codigo,))

    produto = cursor.fetchone()
    conn.close()

    return produto

#Pra usar a função de busca, o codigo precisa ser algo como isso:
# codigo = codigo_lido()
# produto = buscar_por_codigo_barras(codigo)

def buscar_por_nome(nome):
    conn = conectar()
    cursor = conn.execute("""
        SELECT *
        FROM produto
        WHERE nome_produto LIKE ?
    """, (f"%{nome}%",))

    produtos = cursor.fetchall()
    conn.close()

    return produtos

def buscar_por_id(id_produto):
    conn = conectar()
    cursor = conn.execute("""
        SELECT *
        FROM produto
        WHERE id_produto = ?
    """, (id_produto,))

    produto = cursor.fetchone()
    conn.close()

    return produto

def buscar_nome_por_id(id_produto):
    conn = conectar()
    cursor = conn.execute("""
        SELECT nome_produto
        FROM produto
        WHERE id_produto = ?
    """, (id_produto,))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None

def buscar_categoria_por_id(id_produto):
    conn = conectar()
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
    conn = conectar()
    cursor = conn.execute("""
        SELECT codigo_barras
        FROM produto
        WHERE id_produto = ?
    """, (id_produto,))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None

def buscar_quantidade_por_id(id_produto):
    conn = conectar()
    cursor = conn.execute("""
        SELECT quantidade
        FROM produto
        WHERE id_produto = ?
    """, (id_produto,))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None

def buscar_medida_quantidade_por_id(id_produto):
    conn = conectar()
    cursor = conn.execute("""
        SELECT medida_quantidade
        FROM produto
        WHERE id_produto = ?
    """, (id_produto,))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None

def buscar_unidade_por_id(id_produto):
    conn = conectar()
    cursor = conn.execute("""
        SELECT unidade
        FROM produto
        WHERE id_produto = ?
    """, (id_produto,))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None

def buscar_valor_unitario_por_id(id_produto):
    conn = conectar()
    cursor = conn.execute("""
        SELECT valor_unitario
        FROM produto
        WHERE id_produto = ?
    """, (id_produto,))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None

def listar_todos():
    conn = conectar()
    cursor = conn.execute("""
        SELECT *
        FROM produto
        ORDER BY nome_produto
    """)

    produtos = cursor.fetchall()
    conn.close()

    return produtos

#pra chamar o listar_todos seria algo como isso:
# produtos = listar_todos()
# for produto in produtos:
#    print(produto)