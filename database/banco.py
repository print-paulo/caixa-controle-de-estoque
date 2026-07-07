import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco


def criar_tabelas(conn): # Cria as tabelas categoria, produto, estoque, venda, item_venda, compra e item_compra no banco SQLite, se não existirem.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categoria (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_categoria TEXT NOT NULL UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS produto (
            id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo INTEGER NOT NULL DEFAULT 1,
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS venda (
            id_venda INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            forma_pagamento TEXT,
            status TEXT NOT NULL DEFAULT 'aberta'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS item_venda (
            id_item_venda INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venda INTEGER NOT NULL,
            id_produto INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario_momento REAL NOT NULL,
            sub_total REAL NOT NULL,
            FOREIGN KEY (id_venda) REFERENCES venda(id_venda),
            FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS compra (
            id_compra INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fornecedor TEXT,
            status TEXT NOT NULL DEFAULT 'aberta'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS item_compra (
            id_item_compra INTEGER PRIMARY KEY AUTOINCREMENT,
            id_compra INTEGER NOT NULL,
            id_produto INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_custo_unitario REAL NOT NULL,
            margem_lucro REAL NOT NULL,
            valor_venda_calculado REAL NOT NULL,
            sub_total REAL NOT NULL,
            FOREIGN KEY (id_compra) REFERENCES compra(id_compra),
            FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
        )
    """)
    conn.commit()

if __name__ == "__main__":
    conn = conectar_banco() # Conecta ao banco SQLite, criando o arquivo se não existir
    criar_tabelas(conn)