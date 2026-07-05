import sqlite3
from pathlib import Path

PASTA_SCRIPT = Path(__file__).resolve().parent
BANCO = PASTA_SCRIPT.parent / "database" / "banco.db"

def conectar():
    conn = sqlite3.connect(BANCO)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def excluir_produto(id_produto):
    conn = conectar()
    try:
        cursor = conn.execute("""
            UPDATE produto
            SET ativo = 0
            WHERE id_produto = ?
            AND ativo = 1
        """, (id_produto,))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()


def reativar_produto(id_produto):
    conn = conectar()
    try:
        cursor = conn.execute("""
            UPDATE produto
            SET ativo = 1
            WHERE id_produto = ?
            AND ativo = 0
        """, (id_produto,))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()