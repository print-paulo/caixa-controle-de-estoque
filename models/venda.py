from dataclasses import dataclass
from typing import Optional


@dataclass
class Venda:
    """Representa uma linha da tabela `venda`."""
    id_venda: int
    data_hora: str
    forma_pagamento: Optional[str]
    valor_total: Optional[float]
    status: str

    @classmethod
    def from_row(cls, row):
        """Converte um sqlite3.Row (de `SELECT * FROM venda`) numa Venda."""
        if row is None:
            return None
        return cls(
            id_venda=row["id_venda"],
            data_hora=row["data_hora"],
            forma_pagamento=row["forma_pagamento"],
            valor_total=row["valor_total"],
            status=row["status"],
        )

    @classmethod
    def from_rows(cls, rows):
        """Converte uma lista de sqlite3.Row (mesmo formato de from_row) numa lista de Venda."""
        return [cls.from_row(row) for row in rows]