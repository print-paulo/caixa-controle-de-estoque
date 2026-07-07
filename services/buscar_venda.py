import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco


def buscar_venda_por_id(id_venda):
    """Busca os dados de uma venda (id_venda, data_hora, forma_pagamento, status)."""
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT *
        FROM venda
        WHERE id_venda = ?
    """, (id_venda,))

    venda = cursor.fetchone()
    conn.close()

    return venda


def listar_itens_venda(id_venda):
    """
    Lista os itens de uma venda, já com o nome do produto (via JOIN),
    útil pra montar um recibo ou conferir o que foi vendido.
    """
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT iv.id_item_venda, iv.id_produto, p.nome_produto, iv.quantidade,
               iv.valor_unitario_momento, iv.sub_total
        FROM item_venda iv
        JOIN produto p ON p.id_produto = iv.id_produto
        WHERE iv.id_venda = ?
    """, (id_venda,))

    itens = cursor.fetchall()
    conn.close()

    return itens


def listar_vendas(status=None):
    """
    Lista vendas, da mais recente pra mais antiga.
    Se `status` for informado (ex: 'finalizada', 'aberta', 'cancelada'),
    filtra só por esse status.
    """
    conn = conectar_banco()

    if status:
        cursor = conn.execute("""
            SELECT *
            FROM venda
            WHERE status = ?
            ORDER BY data_hora DESC, id_venda DESC
        """, (status,))
    else:
        cursor = conn.execute("""
            SELECT *
            FROM venda
            ORDER BY data_hora DESC, id_venda DESC
        """)

    vendas = cursor.fetchall()
    conn.close()

    return vendas


def listar_vendas_por_produto(id_produto):
    """
    Lista o histórico de vendas de um produto específico: cada item de
    venda em que ele apareceu, com a data da venda, mais recente primeiro.
    """
    conn = conectar_banco()
    cursor = conn.execute("""
        SELECT iv.id_item_venda, iv.id_venda, v.data_hora, iv.quantidade,
               iv.valor_unitario_momento, iv.sub_total
        FROM item_venda iv
        JOIN venda v ON v.id_venda = iv.id_venda
        WHERE iv.id_produto = ?
        ORDER BY v.data_hora DESC, v.id_venda DESC
    """, (id_produto,))

    itens = cursor.fetchall()
    conn.close()

    return itens