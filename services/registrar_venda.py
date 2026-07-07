import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco
from utils.validacoes import validar_positivo


def iniciar_venda():
    """Cria uma nova venda com status 'aberta' e retorna o id_venda."""
    conn = conectar_banco()
    try:
        cursor = conn.execute("INSERT INTO venda (status) VALUES ('ABERTA')")
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def adicionar_item_venda(id_venda, codigo_barras, quantidade):
    """
    Adiciona um item a uma venda em aberto, a partir do código de barras lido.

    Busca o produto ativo, confere se há estoque de exposição suficiente,
    calcula o sub_total com o valor unitário atual (congelado no momento
    da venda) e desconta a quantidade do estoque de exposição.
    Tudo numa única transação: se qualquer passo falhar, nada é salvo.

    Retorna o sub_total do item adicionado.
    """
    validar_positivo(quantidade, "Quantidade vendida")

    conn = conectar_banco()
    try:
        venda = conn.execute(
            "SELECT status FROM venda WHERE id_venda = ?", (id_venda,)
        ).fetchone()
        if venda is None:
            raise ValueError(f"Venda {id_venda} não encontrada.")
        if venda[0] != "ABERTA":
            raise ValueError(f"Venda {id_venda} não está aberta (status atual: '{venda[0]}').")

        produto = conn.execute("""
            SELECT id_produto, nome_produto, valor_unitario
            FROM produto
            WHERE codigo_barras = ? AND ativo = 1
        """, (codigo_barras,)).fetchone()

        if produto is None:
            raise ValueError(f"Produto com código de barras '{codigo_barras}' não encontrado.")

        id_produto, nome_produto, valor_unitario = produto

        if valor_unitario is None:
            raise ValueError(f"Produto '{nome_produto}' não tem valor unitário cadastrado.")

        estoque = conn.execute(
            "SELECT estoque_exposicao FROM estoque WHERE id_produto = ?", (id_produto,)
        ).fetchone()
        estoque_atual = estoque[0] if estoque and estoque[0] is not None else 0

        if estoque_atual < quantidade:
            raise ValueError(
                f"Estoque insuficiente para '{nome_produto}': "
                f"disponível {estoque_atual}, solicitado {quantidade}."
            )

        sub_total = quantidade * valor_unitario

        conn.execute("""
            INSERT INTO item_venda (id_venda, id_produto, quantidade, valor_unitario_momento, sub_total)
            VALUES (?, ?, ?, ?, ?)
        """, (id_venda, id_produto, quantidade, valor_unitario, sub_total))

        conn.execute("""
            UPDATE estoque
            SET estoque_exposicao = estoque_exposicao - ?, ultima_atualizacao = CURRENT_TIMESTAMP
            WHERE id_produto = ?
        """, (quantidade, id_produto))

        conn.commit()
        return sub_total

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def calcular_total_venda(id_venda):
    """Soma os sub_total de todos os itens da venda. Retorna 0.0 se não houver itens."""
    conn = conectar_banco()
    try:
        total = conn.execute(
            "SELECT SUM(sub_total) FROM item_venda WHERE id_venda = ?", (id_venda,)
        ).fetchone()[0]
        return total or 0.0
    finally:
        conn.close()


def finalizar_venda(id_venda, forma_pagamento):
    """
    Marca a venda como 'FINALIZADA' e registra a forma de pagamento.
    Recusa finalizar vendas sem nenhum item. Retorna o valor total da venda.
    """
    if not forma_pagamento or not forma_pagamento.strip():
        raise ValueError("Forma de pagamento não pode ser vazia.")

    conn = conectar_banco()
    try:
        tem_item = conn.execute(
            "SELECT 1 FROM item_venda WHERE id_venda = ?", (id_venda,)
        ).fetchone()
        if tem_item is None:
            raise ValueError("Não é possível finalizar uma venda sem itens.")

        conn.execute(
            "UPDATE venda SET forma_pagamento = ?, status = 'FINALIZADA' WHERE id_venda = ?",
            (forma_pagamento.strip(), id_venda),
        )
        conn.commit()
    finally:
        conn.close()

    return calcular_total_venda(id_venda)


def cancelar_venda(id_venda):
    """Cancela a venda em aberto e devolve os itens já lidos ao estoque de exposição."""
    conn = conectar_banco()
    try:
        itens = conn.execute(
            "SELECT id_produto, quantidade FROM item_venda WHERE id_venda = ?", (id_venda,)
        ).fetchall()

        for id_produto, quantidade in itens:
            conn.execute("""
                UPDATE estoque
                SET estoque_exposicao = estoque_exposicao + ?, ultima_atualizacao = CURRENT_TIMESTAMP
                WHERE id_produto = ?
            """, (quantidade, id_produto))

        conn.execute("UPDATE venda SET status = 'CANCELADA' WHERE id_venda = ?", (id_venda,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()