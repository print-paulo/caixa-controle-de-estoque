from dataclasses import dataclass
from typing import Optional


@dataclass
class Produto:
    id_produto: int
    ativo: bool
    id_categoria: Optional[int]
    codigo_barras: Optional[str]
    nome_produto: str
    medida_embalagem: Optional[str]
    unidade: Optional[str]
    valor_unitario: Optional[float]
    custo_unitario: Optional[float]

    @classmethod
    def from_row(cls, row):
        """Converte um sqlite3.Row (de `SELECT * FROM produto`) num Produto."""
        if row is None:
            return None
        return cls(
            id_produto=row["id_produto"],
            ativo=bool(row["ativo"]),
            id_categoria=row["id_categoria"],
            codigo_barras=row["codigo_barras"],
            nome_produto=row["nome_produto"],
            medida_embalagem=row["medida_embalagem"],
            unidade=row["unidade"],
            valor_unitario=row["valor_unitario"],
            custo_unitario=row["custo_unitario"],
        )

    @classmethod
    def from_rows(cls, rows):
        """Converte uma lista de sqlite3.Row (de `SELECT * FROM produto`) numa lista de Produto."""
        return [cls.from_row(row) for row in rows]