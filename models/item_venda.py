from dataclasses import dataclass


@dataclass
class ItemVenda:
    """
    Representa um item de venda, já com o nome do produto embutido
    (denormalizado via JOIN com `produto`) -- mesmo formato que
    `listar_itens_venda` já devolvia, só que agora incluindo também
    `id_venda` (que a query original não selecionava, por já vir como
    parâmetro do caller, mas fica mais fiel à entidade tê-lo aqui).
    """
    id_item_venda: int
    id_venda: int
    id_produto: int
    nome_produto: str
    quantidade: int
    valor_unitario_momento: float
    sub_total: float

    @classmethod
    def from_row(cls, row):
        """
        Converte um sqlite3.Row vindo do JOIN `item_venda iv JOIN produto p`
        (colunas: id_item_venda, id_venda, id_produto, nome_produto,
        quantidade, valor_unitario_momento, sub_total) num ItemVenda.
        """
        if row is None:
            return None
        return cls(
            id_item_venda=row["id_item_venda"],
            id_venda=row["id_venda"],
            id_produto=row["id_produto"],
            nome_produto=row["nome_produto"],
            quantidade=row["quantidade"],
            valor_unitario_momento=row["valor_unitario_momento"],
            sub_total=row["sub_total"],
        )

    @classmethod
    def from_rows(cls, rows):
        """Converte uma lista de sqlite3.Row (mesmo formato de from_row) numa lista de ItemVenda."""
        return [cls.from_row(row) for row in rows]