import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco
from utils.validacoes import validar_positivo, validar_nao_negativo
from services.estoque import registrar_movimento, ajustar_estoque_deposito


def iniciar_compra(fornecedor=None):
    """Cria uma nova compra com status 'ABERTA' e retorna o id_compra."""
    conn = conectar_banco()
    try:
        cursor = conn.execute(
            "INSERT INTO compra (fornecedor, status) VALUES (?, 'ABERTA')", (fornecedor,)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def _validar_compra_aberta(conn, id_compra):
    compra = conn.execute(
        "SELECT status FROM compra WHERE id_compra = ?", (id_compra,)
    ).fetchone()
    if compra is None:
        raise ValueError(f"Compra {id_compra} não encontrada.")
    if compra[0] != "ABERTA":
        raise ValueError(f"Compra {id_compra} não está aberta (status atual: {compra[0]}).")


def adicionar_item_compra(id_compra, codigo_barras, quantidade, valor_custo_unitario, margem_lucro):
    """
    Adiciona um item a uma compra em aberto, a partir do código de barras do produto.

    - quantidade: unidades compradas (deve ser maior que zero)
    - valor_custo_unitario: quanto custou cada unidade nessa compra
    - margem_lucro: fração de lucro desejada sobre o custo (ex: 0.3 = 30%)

    Calcula o valor de venda sugerido (custo * (1 + margem)), congela esse
    valor e a margem usada no momento da compra, soma a quantidade ao
    estoque de depósito e já atualiza o valor_unitario de venda do produto.
    Tudo numa única transação: se qualquer passo falhar, nada é salvo.

    Retorna uma tupla (sub_total_custo, valor_venda_calculado).
    """
    validar_positivo(quantidade, "Quantidade comprada")
    validar_nao_negativo(valor_custo_unitario, "Valor de custo unitário", permitir_none=False)
    validar_nao_negativo(margem_lucro, "Margem de lucro", permitir_none=False)

    conn = conectar_banco()
    try:
        _validar_compra_aberta(conn, id_compra)

        produto = conn.execute("""
            SELECT id_produto, nome_produto
            FROM produto
            WHERE codigo_barras = ? AND ativo = 1
        """, (codigo_barras,)).fetchone()

        if produto is None:
            raise ValueError(f"Produto com código de barras '{codigo_barras}' não encontrado.")

        id_produto, nome_produto = produto

        valor_venda_calculado = valor_custo_unitario * (1 + margem_lucro)
        sub_total = quantidade * valor_custo_unitario

        conn.execute("""
            INSERT INTO item_compra (
                id_compra, id_produto, quantidade,
                valor_custo_unitario, margem_lucro, valor_venda_calculado, sub_total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id_compra, id_produto, quantidade, valor_custo_unitario, margem_lucro, valor_venda_calculado, sub_total))

        conn.execute("""
            UPDATE estoque
            SET estoque_deposito = estoque_deposito + ?, ultima_atualizacao = CURRENT_TIMESTAMP
            WHERE id_produto = ?
        """, (quantidade, id_produto))

        registrar_movimento(conn, id_produto, "COMPRA", "estoque_deposito", quantidade, id_compra)

        conn.execute(
            "UPDATE produto SET valor_unitario = ? WHERE id_produto = ?",
            (valor_venda_calculado, id_produto),
        )

        conn.commit()
        return sub_total, valor_venda_calculado

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def calcular_total_compra(id_compra):
    """Soma o sub_total (custo) de todos os itens da compra. Retorna 0.0 se não houver itens."""
    conn = conectar_banco()
    try:
        total = conn.execute(
            "SELECT SUM(sub_total) FROM item_compra WHERE id_compra = ?", (id_compra,)
        ).fetchone()[0]
        return total or 0.0
    finally:
        conn.close()


def finalizar_compra(id_compra):
    """
    Marca a compra como 'FINALIZADA'. Recusa finalizar compras sem nenhum item.
    Retorna o valor total (em custo) da compra.
    """
    conn = conectar_banco()
    try:
        tem_item = conn.execute(
            "SELECT 1 FROM item_compra WHERE id_compra = ?", (id_compra,)
        ).fetchone()
        if tem_item is None:
            raise ValueError("Não é possível finalizar uma compra sem itens.")

        conn.execute(
            "UPDATE compra SET status = 'FINALIZADA' WHERE id_compra = ?", (id_compra,)
        )
        conn.commit()
    finally:
        conn.close()

    return calcular_total_compra(id_compra)


def cancelar_compra(id_compra):
    """
    Cancela a compra em aberto e retira do estoque de depósito a quantidade
    que havia sido somada por cada item.

    Observação: não reverte o valor_unitario do produto que possa ter sido
    atualizado por essa compra, já que outra compra ou edição manual pode
    ter mudado o preço depois. Se precisar, ajuste o valor manualmente.
    """
    conn = conectar_banco()
    try:
        _validar_compra_aberta(conn, id_compra)
        itens = conn.execute(
            "SELECT id_produto, quantidade FROM item_compra WHERE id_compra = ?", (id_compra,)
        ).fetchall()

        for id_produto, quantidade in itens:
            ajustar_estoque_deposito(
                id_produto, -quantidade,
                conn=conn, tipo="CANCELAMENTO_COMPRA", origem_id=id_compra,
                exigir_produto_ativo=False,
            )

        conn.execute("UPDATE compra SET status = 'CANCELADA' WHERE id_compra = ?", (id_compra,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()