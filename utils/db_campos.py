import sqlite3

from utils.conectar_banco import conectar_banco


def atualizar_campo_produto(id_produto, coluna, valor, contexto="atualizar", validar_existe=None):
    """
    Faz o UPDATE de uma única coluna da tabela produto.

    - contexto: usado na mensagem de erro (ex: "Erro ao {contexto} {coluna}").
    - validar_existe: função opcional que recebe id_produto e levanta
      ValueError se o produto não existir (usada na edição, não no cadastro).
    """
    if validar_existe is not None:
        validar_existe(id_produto)

    conn = conectar_banco()
    try:
        conn.execute(f"UPDATE produto SET {coluna} = ? WHERE id_produto = ?", (valor, id_produto))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao {contexto} {coluna}: {e}")
    finally:
        conn.close()


def atualizar_campo_estoque(id_produto, coluna, valor, contexto="atualizar", exigir_existente=False):
    """
    Faz o UPDATE de uma única coluna da tabela estoque.

    - contexto: usado na mensagem de erro (ex: "Erro ao {contexto} {coluna}").
    - exigir_existente: se True, valida que já existe uma linha de estoque
      para o produto antes de atualizar (usada na edição, não no cadastro).
    """
    conn = conectar_banco()
    try:
        if exigir_existente:
            existe = conn.execute(
                "SELECT 1 FROM estoque WHERE id_produto = ?", (id_produto,)
            ).fetchone()
            if existe is None:
                raise ValueError(f"Não existe linha de estoque para o produto {id_produto}.")

        conn.execute(
            f"UPDATE estoque SET {coluna} = ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id_produto = ?",
            (valor, id_produto),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao {contexto} {coluna}: {e}")
    finally:
        conn.close()