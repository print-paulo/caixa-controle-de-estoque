import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco


def buscar_compra_por_id(id_compra):
    """Busca os dados de uma compra (id_compra, data_hora, fornecedor, status)."""
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT *
        FROM compra
        WHERE id_compra = ?
    """, (id_compra,))

    compra = cursor.fetchone()
    conn.close()

    return compra


def listar_itens_compra(id_compra):
    """
    Lista os itens de uma compra, já com o nome do produto (via JOIN),
    útil pra conferir o que foi recebido do fornecedor.
    """
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT ic.id_item_compra, ic.id_produto, p.nome_produto, ic.quantidade,
               ic.valor_custo_unitario, ic.margem_lucro, ic.valor_venda_calculado, ic.sub_total
        FROM item_compra ic
        JOIN produto p ON p.id_produto = ic.id_produto
        WHERE ic.id_compra = ?
    """, (id_compra,))

    itens = cursor.fetchall()
    conn.close()

    return itens


def listar_compras(status=None):
    """
    Lista compras, da mais recente pra mais antiga.
    Se `status` for informado (ex: 'ABERTA', 'FINALIZADA', 'CANCELADA'),
    filtra só por esse status.
    """
    conn = conectar_banco()

    if status:
        cursor = conn.execute("""
            SELECT *
            FROM compra
            WHERE status = ?
            ORDER BY data_hora DESC, id_compra DESC
        """, (status,))
    else:
        cursor = conn.execute("""
            SELECT *
            FROM compra
            ORDER BY data_hora DESC, id_compra DESC
        """)

    compras = cursor.fetchall()
    conn.close()

    return compras


def listar_compras_por_produto(id_produto):
    """
    Lista o histórico de compras de um produto específico: cada item de
    compra em que ele apareceu, com a data da compra, mais recente primeiro.
    """
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT ic.id_item_compra, ic.id_compra, c.data_hora, ic.quantidade,
               ic.valor_custo_unitario, ic.valor_venda_calculado, ic.sub_total
        FROM item_compra ic
        JOIN compra c ON c.id_compra = ic.id_compra
        WHERE ic.id_produto = ?
        ORDER BY c.data_hora DESC, c.id_compra DESC
    """, (id_produto,))

    itens = cursor.fetchall()
    conn.close()

    return itens