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
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco
from database.banco import criar_tabelas

PASTA_SCRIPT = Path(__file__).resolve().parent # Caminho absoluto da pasta onde está este script
PASTA_PLANILHAS = Path("../planilhas").resolve() # Caminho absoluto da pasta "planilha" ao lado deste script
BANCO = PASTA_SCRIPT / "banco.db" # Caminho absoluto do banco SQLite a ser criado na mesma pasta deste script


def separar_quantidade(valor): # Separa o valor da quantidade do texto.
    """'750 ml' -> (750.0, 'ml'). Se não der pra separar, devolve (None, texto original)."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None, None
    texto = str(valor).strip().upper()
    match = re.match(r"([\d.,]+)\s*([a-zA-Zçã]*)", texto)
    if match and match.group(1):
        numero = match.group(1).replace(",", ".")
        try:
            return float(numero), (match.group(2) or None)
        except ValueError:
            return None, texto
    return None, texto


def linha_valida(row): # Verifica se uma linha da planilha é válida.
    """Descarta linhas vazias, a linha de total e linhas com nome de produto inválido."""
    produto = row["Produto"]
    if produto is None or (isinstance(produto, float) and pd.isna(produto)):
        return False
    if not isinstance(produto, str) or not produto.strip():
        return False
    return True


def importar_arquivo(cursor, caminho_arquivo): # Importa um único arquivo .xlsx para o banco SQLite.
    """Importa um único .xlsx e devolve (inseridos, ignorados) desse arquivo."""
    df = pd.read_excel(caminho_arquivo, sheet_name=0, header=1)

    inseridos = 0
    ignorados = 0

    for _, row in df.iterrows():
        if not linha_valida(row):
            ignorados += 1
            continue

        # codigo_barras fica sempre nulo aqui - será preenchido manualmente depois via UPDATE
        codigo = None
        nome_produto = str(row["Produto"]).strip()
        quantidade, medida = separar_quantidade(row.get("Quantidade"))
        unidade = str(row["Unidade"]).strip() if pd.notna(row.get("Unidade")) else None
        minimo = int(row["Estoque Mínimo"]) if pd.notna(row.get("Estoque Mínimo")) else 0
        # A planilha só tem "Estoque Atual" (um valor só), sem distinguir depósito/exposição.
        # Assumindo esse valor como estoque_deposito por enquanto; ajuste manualmente depois se necessário.
        estoque_deposito = int(row["Estoque Atual"]) if pd.notna(row.get("Estoque Atual")) else 0
        estoque_exposicao = 0
        capacidade_exposicao = None
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
            INSERT INTO estoque
            (id_produto, estoque_deposito, estoque_exposicao, capacidade_exposicao, estoque_minimo, ultima_atualizacao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_produto, estoque_deposito, estoque_exposicao, capacidade_exposicao, minimo,
              str(ultima_atualizacao) if ultima_atualizacao else None))

        inseridos += 1

    return inseridos, ignorados


def importar(): # Função principal que importa todos os arquivos .xlsx da pasta "planilha" para o banco SQLite.
    if not PASTA_PLANILHAS.exists():
        print(f"Pasta não encontrada: {PASTA_PLANILHAS}")
        print("Crie uma pasta 'planilha' ao lado deste script e coloque os .xlsx dentro dela.")
        return

    # ignora arquivos temporários do Excel (ex: ~$Estoque.xlsx, criados quando o arquivo está aberto)
    arquivos = [
        f for f in PASTA_PLANILHAS.glob("*.xlsx")
        if not f.name.startswith("~$")
    ]

    if not arquivos:
        print(f"Nenhum .xlsx encontrado em: {PASTA_PLANILHAS}")
        return

    conn = conectar_banco() # Conecta ao banco SQLite, criando o arquivo se não existir
    conn.execute("PRAGMA foreign_keys = ON")
    criar_tabelas(conn)
    cursor = conn.cursor()

    total_inseridos = 0
    total_ignorados = 0

    for arquivo in arquivos:
        try:
            inseridos, ignorados = importar_arquivo(cursor, arquivo)
        except Exception as e:
            print(f"Erro ao importar '{arquivo.name}': {e}")
            continue

        total_inseridos += inseridos
        total_ignorados += ignorados
        print(f"  {arquivo.name}: {inseridos} inseridos, {ignorados} ignorados")

    conn.commit()
    conn.close()

    print(f"\nBanco criado em: {BANCO}")
    print(f"Importação concluída: {total_inseridos} produtos inseridos no total, "
          f"{total_ignorados} linhas ignoradas (vazias/inválidas).")


if __name__ == "__main__":
    importar()