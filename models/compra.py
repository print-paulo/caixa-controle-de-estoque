from dataclasses import dataclass
from typing import Optional


@dataclass
class Compra:
    """Representa uma linha da tabela `compra`."""
    id_compra: int
    data_hora: str
    fornecedor: Optional[str]
    status: str

    @classmethod
    def from_row(cls, row):
        """Converte um sqlite3.Row (de `SELECT * FROM compra`) numa Compra."""
        if row is None:
            return None
        return cls(
            id_compra=row["id_compra"],
            data_hora=row["data_hora"],
            fornecedor=row["fornecedor"],
            status=row["status"],
        )

    @classmethod
    def from_rows(cls, rows):
        """Converte uma lista de sqlite3.Row (mesmo formato de from_row) numa lista de Compra."""
        return [cls.from_row(row) for row in rows]