import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco
from utils.validacoes import validar_nao_negativo


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


def cadastrar_produto_completo(
    nome_produto,
    nome_categoria=None,
    codigo_barras=None,
    medida_embalagem=None,
    unidade=None,
    capacidade_exposicao=None,
    estoque_minimo=None,
):
    """
    Cria o produto inteiro (linha em `produto` + linha em `estoque`) numa
    ÚNICA transação: uma conexão, um commit no final, rollback em
    qualquer erro -- inclusive interrupções como Ctrl+C, o terminal
    fechar, ou queda de energia no meio da chamada.

    Diferente do cadastro antigo (uma chamada -- e um commit -- por
    campo, espalhadas ao longo de toda a conversa com o usuário), aqui
    não existe "produto pela metade": ou o cadastro inteiro é salvo, ou
    nada é. Por isso esta função espera receber TODOS os dados já
    coletados e validados (tipo/formato) pelo chamador -- o controller
    deve pedir tudo ao usuário antes, em memória, e só então chamar esta
    função uma única vez.

    Levanta ValueError se o nome estiver vazio, se algum valor numérico
    for negativo, ou se o código de barras já estiver em uso.
    Retorna o id_produto criado.
    """
    if not nome_produto or not nome_produto.strip():
        raise ValueError("Nome do produto não pode ser vazio.")

    validar_nao_negativo(capacidade_exposicao, "Capacidade de exposição", feminino=True)
    validar_nao_negativo(estoque_minimo, "Estoque mínimo")

    conn = conectar_banco()
    try:
        if codigo_barras:
            existe = conn.execute(
                "SELECT 1 FROM produto WHERE codigo_barras = ? AND ativo = 1", (codigo_barras,)
            ).fetchone()
            if existe:
                raise ValueError(f"O código de barras '{codigo_barras}' já está cadastrado.")

        id_categoria = obter_ou_criar_categoria(conn, nome_categoria)

        cursor = conn.execute("""
            INSERT INTO produto (id_categoria, codigo_barras, nome_produto, medida_embalagem, unidade)
            VALUES (?, ?, ?, ?, ?)
        """, (id_categoria, codigo_barras, nome_produto.strip(), medida_embalagem, unidade))
        id_produto = cursor.lastrowid

        conn.execute("""
            INSERT INTO estoque
            (id_produto, estoque_deposito, estoque_exposicao, capacidade_exposicao, estoque_minimo, ultima_atualizacao)
            VALUES (?, 0, 0, ?, ?, CURRENT_TIMESTAMP)
        """, (id_produto, capacidade_exposicao, estoque_minimo))

        conn.commit()
        return id_produto

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao cadastrar produto: {e}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()