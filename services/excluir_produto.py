import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco


def _definir_ativo(id_produto, ativo):
    """Função interna: alterna o campo `ativo` do produto, indo de/para o estado oposto."""
    conn = conectar_banco()
    try:
        cursor = conn.execute("""
            UPDATE produto
            SET ativo = ?
            WHERE id_produto = ?
            AND ativo = ?
        """, (ativo, id_produto, 1 - ativo))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()


def excluir_produto(id_produto):
    return _definir_ativo(id_produto, ativo=0)


def reativar_produto(id_produto):
    return _definir_ativo(id_produto, ativo=1)