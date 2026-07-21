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
      para o produto E que o produto está ativo (usada na edição, não no
      cadastro -- produto desativado é tratado como "excluído", então seu
      estoque não deve poder ser editado).
    """
    conn = conectar_banco()
    try:
        if exigir_existente:
            resultado = conn.execute("""
                SELECT p.ativo
                FROM estoque e
                JOIN produto p ON p.id_produto = e.id_produto
                WHERE e.id_produto = ?
            """, (id_produto,)).fetchone()

            if resultado is None:
                raise ValueError(f"Não existe linha de estoque para o produto {id_produto}.")

            if resultado[0] != 1:
                raise ValueError(
                    f"Produto com id {id_produto} está desativado; não é possível editar seu estoque."
                )

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