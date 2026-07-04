import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.leitor_barras import codigo_lido

# services/ e database/ são pastas irmãs, então sobe um nível e desce em database/
PASTA_SCRIPT = Path(__file__).resolve().parent
BANCO = PASTA_SCRIPT.parent / "database" / "banco.db"


def conectar():
    conn = sqlite3.connect(BANCO)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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


def cadastrar_produto(
    nome_produto,
    categoria=None,
    quantidade=None,
    medida_quantidade=None,
    unidade=None,
    valor_unitario=0.0,
    estoque_deposito=0,
    estoque_exposicao=0,
    capacidade_exposicao=None,
    estoque_minimo=0,
    codigo_barras=None,
):
    """Cadastra um novo produto + sua linha de estoque. Retorna o id_produto criado."""
    if not nome_produto or not nome_produto.strip():
        raise ValueError("Nome do produto não pode ser vazio.")
    if valor_unitario < 0:
        raise ValueError("Valor unitário não pode ser negativo.")

    conn = conectar()
    try:
        id_categoria = obter_ou_criar_categoria(conn, categoria)

        cursor = conn.execute("""
            INSERT INTO produto
            (id_categoria, codigo_barras, nome_produto, quantidade, medida_quantidade, unidade, valor_unitario)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id_categoria, codigo_barras, nome_produto.strip(), quantidade, medida_quantidade, unidade, valor_unitario))
        id_produto = cursor.lastrowid

        conn.execute("""
            INSERT INTO estoque
            (id_produto, estoque_deposito, estoque_exposicao, capacidade_exposicao, estoque_minimo, ultima_atualizacao)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (id_produto, estoque_deposito, estoque_exposicao, capacidade_exposicao, estoque_minimo))

        conn.commit()
        return id_produto
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao cadastrar produto: {e}")
    finally:
        conn.close()
        
# Teste rápido para verificar se o cadastro funciona
if __name__ == "__main__":
    id_produto = cadastrar_produto(
        nome_produto="Coca-Cola 2L",
        categoria="Bebidas",
        quantidade=2.0,
        medida_quantidade="L",
        unidade="UN",
        valor_unitario=8.5,
        estoque_deposito=10,
        estoque_minimo=3,
        codigo_barras=codigo_lido()
    )
    print(f"Produto cadastrado com id {id_produto}")