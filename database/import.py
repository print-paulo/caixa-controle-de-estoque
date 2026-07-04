"""
Importa dados de estoque de um .xlsx para um banco SQLite.

Uso:
    python importar_estoque.py

Espera um arquivo "Estoque.xlsx" na MESMA PASTA deste script, com a aba
"Controle de Estoque" no formato: Código | Produto | Quantidade | Unidade |
Estoque Mínimo | Estoque Atual | Valor Unitário | Valor Total | Status | Última Atualização
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

PASTA_PLANILHA = Path("../planilhas").resolve()
PASTA_SCRIPT = Path(__file__).resolve().parent
ARQUIVO_EXCEL = PASTA_PLANILHA / "banco.xlsx"
ABA = "Controle de Estoque"
BANCO = PASTA_SCRIPT / "banco.db"


def criar_tabelas(conn):
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
            estoque_minimo INTEGER,
            estoque_atual INTEGER,
            ultima_atualizacao TIMESTAMP,
            FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
        )
    """)
    conn.commit()


def separar_quantidade(valor):
    """'750 ml' -> (750.0, 'ml'). Se não der pra separar, devolve (None, texto original)."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None, None
    texto = str(valor).strip()
    match = re.match(r"([\d.,]+)\s*([a-zA-Zçã]*)", texto)
    if match and match.group(1):
        numero = match.group(1).replace(",", ".")
        try:
            return float(numero), (match.group(2) or None)
        except ValueError:
            return None, texto
    return None, texto


def linha_valida(row):
    """Descarta linhas vazias, a linha de total e linhas com nome de produto inválido."""
    produto = row["Produto"]
    if produto is None or (isinstance(produto, float) and pd.isna(produto)):
        return False
    if not isinstance(produto, str) or not produto.strip():
        return False
    return True


def importar():
    if not ARQUIVO_EXCEL.exists():
        print(f"Arquivo não encontrado: {ARQUIVO_EXCEL}")
        print("Coloque o 'Estoque.xlsx' na mesma pasta deste script.")
        return

    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA, header=1)

    conn = sqlite3.connect(BANCO)
    conn.execute("PRAGMA foreign_keys = ON")
    criar_tabelas(conn)
    cursor = conn.cursor()

    inseridos = 0
    ignorados = 0

    for _, row in df.iterrows():
        if not linha_valida(row):
            ignorados += 1
            continue

        codigo = str(row["Código"]).strip() if pd.notna(row["Código"]) else None
        nome_produto = str(row["Produto"]).strip()
        quantidade, medida = separar_quantidade(row.get("Quantidade"))
        unidade = str(row["Unidade"]).strip() if pd.notna(row.get("Unidade")) else None
        minimo = int(row["Estoque Mínimo"]) if pd.notna(row.get("Estoque Mínimo")) else 0
        atual = int(row["Estoque Atual"]) if pd.notna(row.get("Estoque Atual")) else 0
        valor_unitario = float(row["Valor Unitário"]) if pd.notna(row.get("Valor Unitário")) else 0.0
        ultima_atualizacao = row["Última Atualização"] if pd.notna(row.get("Última Atualização")) else None

        # Sem coluna "Categoria" nesta planilha -> fica sem categoria (id_categoria = NULL)
        cursor.execute("""
            INSERT INTO produto
            (codigo_barras, nome_produto, quantidade, medida_quantidade, unidade, valor_unitario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (codigo, nome_produto, quantidade, medida, unidade, valor_unitario))
        id_produto = cursor.lastrowid

        cursor.execute("""
            INSERT INTO estoque (id_produto, estoque_minimo, estoque_atual, ultima_atualizacao)
            VALUES (?, ?, ?, ?)
        """, (id_produto, minimo, atual, str(ultima_atualizacao) if ultima_atualizacao else None))

        inseridos += 1

    conn.commit()
    conn.close()

    print(f"Banco criado em: {BANCO}")
    print(f"Importação concluída: {inseridos} produtos inseridos, {ignorados} linhas ignoradas (vazias/inválidas).")


if __name__ == "__main__":
    importar()