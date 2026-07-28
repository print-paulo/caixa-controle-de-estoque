from dataclasses import dataclass
from typing import Optional


@dataclass
class MovimentoEstoque:
    """
    Representa uma linha do histórico de movimentação de estoque, já com o
    nome do produto embutido (denormalizado via JOIN com `produto`) --
    mesmo formato que `listar_movimentos` já devolvia.
    """
    id_movimento: int
    id_produto: int
    nome_produto: str
    tipo: str
    campo: str
    quantidade: int
    origem_id: Optional[int]
    data_hora: str

    @classmethod
    def from_row(cls, row):
        """
        Converte um sqlite3.Row vindo do JOIN `movimento_estoque m JOIN produto p`
        (colunas: id_movimento, id_produto, nome_produto, tipo, campo,
        quantidade, origem_id, data_hora) num MovimentoEstoque.
        """
        if row is None:
            return None
        return cls(
            id_movimento=row["id_movimento"],
            id_produto=row["id_produto"],
            nome_produto=row["nome_produto"],
            tipo=row["tipo"],
            campo=row["campo"],
            quantidade=row["quantidade"],
            origem_id=row["origem_id"],
            data_hora=row["data_hora"],
        )

    @classmethod
    def from_rows(cls, rows):
        """Converte uma lista de sqlite3.Row (mesmo formato de from_row) numa lista de MovimentoEstoque."""
        return [cls.from_row(row) for row in rows]