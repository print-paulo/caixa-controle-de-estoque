from dataclasses import dataclass


@dataclass
class Categoria:
    """
    Representa uma linha da tabela `categoria`.

    Scaffold: hoje nenhuma função de `services/` devolve a linha inteira de
    `categoria` pra um controller -- os usos existentes
    (`obter_ou_criar_categoria`, `buscar_categoria_por_id`, `editar_categoria`,
    o relatório por categoria) sempre pegam só `id_categoria` ou só
    `nome_categoria` isoladamente, nunca os dois juntos como entidade. Esse
    model fica pronto pra quando existir uma consulta desse tipo (ex: uma
    tela de "listar categorias" no front).
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