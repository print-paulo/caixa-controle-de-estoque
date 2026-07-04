import sqlite3
from pathlib import Path


PASTA_SCRIPT = Path(__file__).resolve().parent # Caminho absoluto da pasta onde está este script
BANCO = PASTA_SCRIPT / "banco.db" # Caminho absoluto do banco SQLite a ser criado na mesma pasta deste script


def criar_tabelas(conn): # Cria as tabelas categoria, produto e estoque no banco SQLite, se não existirem.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categoria (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_categoria TEXT NOT NULL UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS produto (
            id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
            id_categoria INTEGER,
            codigo_barras TEXT UNIQUE,
            nome_produto TEXT NOT NULL,
            quantidade REAL,
            medida_quantidade TEXT,
            unidade TEXT,
            valor_unitario REAL,
            FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id_estoque INTEGER PRIMARY KEY AUTOINCREMENT,
            id_produto INTEGER UNIQUE,
            estoque_deposito INTEGER,
            estoque_exposicao INTEGER,
            capacidade_exposicao INTEGER,
            estoque_minimo INTEGER,
            ultima_atualizacao TIMESTAMP,
            FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
        )
    """)
    conn.commit()

if __name__ == "__main__":
    criar_tabelas(conn=sqlite3.connect(BANCO))