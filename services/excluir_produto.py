import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco


def excluir_produto(id_produto):
    conn = conectar_banco()
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
    conn = conectar_banco()
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