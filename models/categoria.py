from dataclasses import dataclass


@dataclass
class Categoria:
    """
    Representa uma linha da tabela `categoria`.

    Usada por `services/buscar_produto.py::listar_categorias()` -- os
    outros usos (`obter_ou_criar_categoria`, `buscar_categoria_por_id`,
    `editar_categoria`, o relatório por categoria) continuam pegando só
    `id_categoria` ou só `nome_categoria` isoladamente, sem precisar da
    entidade inteira.
    """
    id_categoria: int
    nome_categoria: str

    @classmethod
    def from_row(cls, row):
        """Converte um sqlite3.Row (de `SELECT * FROM categoria`) numa Categoria."""
        if row is None:
            return None
        return cls(
            id_categoria=row["id_categoria"],
            nome_categoria=row["nome_categoria"],
        )

    @classmethod
    def from_rows(cls, rows):
        """Converte uma lista de sqlite3.Row (mesmo formato de from_row) numa lista de Categoria."""
        return [cls.from_row(row) for row in rows]