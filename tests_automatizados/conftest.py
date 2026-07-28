import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import utils.conectar_banco as cb
from database.banco import criar_tabelas


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    """
    Roda ANTES de cada teste: troca o caminho do banco (utils.conectar_banco.BANCO)
    por um arquivo SQLite novo dentro de um diretório temporário do próprio teste
    (tmp_path), já com as tabelas criadas.

    Isso garante que cada teste começa com um banco limpo e isolado -- nenhum
    teste consegue ver ou interferir nos dados de outro, e nada toca no
    database/banco.db de verdade.
    """
    caminho_banco = tmp_path / "banco_teste.db"
    monkeypatch.setattr(cb, "BANCO", str(caminho_banco))

    conn = cb.conectar_banco()
    criar_tabelas(conn)
    conn.close()

    yield


@pytest.fixture
def produto_padrao():
    """
    Cadastra um produto padrão (Vinho Tinto Reserva) pronto pra usar em
    testes de compra/venda/estoque, evitando repetir os mesmos campos em
    todo teste. Retorna o id_produto.
    """
    from services.cadastrar_produto import cadastrar_produto_completo

    return cadastrar_produto_completo(
        nome_produto="Vinho Tinto Reserva",
        nome_categoria="Vinhos",
        codigo_barras="7891234567895",
        medida_embalagem="750ML",
        unidade="UN",
        capacidade_exposicao=10,
        estoque_minimo=3,
    )
