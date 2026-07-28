from dataclasses import dataclass


@dataclass
class ItemCompra:
    """
    Representa um item de compra, já com o nome do produto embutido
    (denormalizado via JOIN com `produto`) -- mesmo formato que
    `listar_itens_compra` já devolvia, só que agora incluindo também
    `id_compra` (que a query original não selecionava, por já vir como
    parâmetro do caller, mas fica mais fiel à entidade tê-lo aqui).
    """
    id_item_compra: int
    id_compra: int
    id_produto: int
    nome_produto: str
    quantidade: int
    valor_custo_unitario: float
    margem_lucro: float
    valor_venda_calculado: float
    sub_total: float

    @classmethod
    def from_row(cls, row):
        """
        Converte um sqlite3.Row vindo do JOIN `item_compra ic JOIN produto p`
        (colunas: id_item_compra, id_compra, id_produto, nome_produto,
        quantidade, valor_custo_unitario, margem_lucro, valor_venda_calculado,
        sub_total) num ItemCompra.
        """
        if row is None:
            return None
        return cls(
            id_item_compra=row["id_item_compra"],
            id_compra=row["id_compra"],
            id_produto=row["id_produto"],
            nome_produto=row["nome_produto"],
            quantidade=row["quantidade"],
            valor_custo_unitario=row["valor_custo_unitario"],
            margem_lucro=row["margem_lucro"],
            valor_venda_calculado=row["valor_venda_calculado"],
            sub_total=row["sub_total"],
        )

    @classmethod
    def from_rows(cls, rows):
        """Converte uma lista de sqlite3.Row (mesmo formato de from_row) numa lista de ItemCompra."""
        return [cls.from_row(row) for row in rows]