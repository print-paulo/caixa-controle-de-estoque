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