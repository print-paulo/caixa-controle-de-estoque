from dataclasses import dataclass
from typing import Optional


@dataclass
class Estoque:
    """
    Representa o estoque de um produto, já com o nome do produto embutido
    (denormalizado via JOIN com `produto`) -- é o mesmo formato que
    `consultar_estoque_por_id`/`listar_estoque_completo` já devolviam antes
    dessa migração.

    Observação: o `id_estoque` (PK própria da tabela `estoque`) não aparece
    aqui de propósito -- ele não é usado em nenhum lugar do projeto, já que
    tudo é referenciado por `id_produto` (que é UNIQUE em `estoque`, ou seja,
    1 produto = 1 linha de estoque). Se algum dia isso mudar (histórico de
    estoque por lote, por exemplo), aí sim vale expor o `id_estoque`.
    """
    id_produto: int
    nome_produto: str
    estoque_deposito: int
    estoque_exposicao: int
    capacidade_exposicao: Optional[int]
    estoque_minimo: Optional[int]
    ultima_atualizacao: Optional[str]

    @classmethod
    def from_row(cls, row):
        """
        Converte um sqlite3.Row vindo do JOIN `estoque e JOIN produto p`
        (colunas: id_produto, nome_produto, estoque_deposito,
        estoque_exposicao, capacidade_exposicao, estoque_minimo,
        ultima_atualizacao) num Estoque.
        """
        if row is None:
            return None
        return cls(
            id_produto=row["id_produto"],
            nome_produto=row["nome_produto"],
            estoque_deposito=row["estoque_deposito"],
            estoque_exposicao=row["estoque_exposicao"],
            capacidade_exposicao=row["capacidade_exposicao"],
            estoque_minimo=row["estoque_minimo"],
            ultima_atualizacao=row["ultima_atualizacao"],
        )

    @classmethod
    def from_rows(cls, rows):
        """Converte uma lista de sqlite3.Row (mesmo formato de from_row) numa lista de Estoque."""
        return [cls.from_row(row) for row in rows]