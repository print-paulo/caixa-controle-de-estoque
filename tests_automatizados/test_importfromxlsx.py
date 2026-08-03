import openpyxl
import pytest

import database.importfromxlsx as imp
from services.buscar_produto import buscar_por_nome
from services.estoque import consultar_estoque_por_id, listar_movimentos
from services.relatorios import relatorio_produtos


def _criar_planilha(tmp_path, linhas, nome_arquivo="Estoque.xlsx"):
    """
    Cria um .xlsx no formato esperado pelo importfromxlsx.py: linha 1 é
    título (ignorada, já que o import usa header=1), linha 2 é o
    cabeçalho de verdade, e as linhas seguintes são os dados.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Controle de Estoque - Planilha Legada"])
    ws.append([
        "Código", "Produto", "Quantidade", "Unidade", "Estoque Mínimo",
        "Estoque Atual", "Valor Unitário", "Valor Total", "Status", "Última Atualização",
    ])
    for linha in linhas:
        ws.append(linha)

    caminho = tmp_path / nome_arquivo
    wb.save(caminho)
    return caminho


@pytest.fixture(autouse=True)
def _pasta_planilhas_isolada(tmp_path, monkeypatch):
    """Isola PASTA_PLANILHAS pra cada teste, sem depender de uma pasta real ao lado do script."""
    pasta = tmp_path / "planilhas"
    pasta.mkdir()
    monkeypatch.setattr(imp, "PASTA_PLANILHAS", pasta)
    return pasta


class TestImportarArquivo:
    def test_importa_produto_com_preco_e_estoque(self, tmp_path):
        caminho = _criar_planilha(tmp_path, [
            [None, "Vinho Legado", "750ML", "UN", 5, 12, 39.9, 478.8, "OK", "2025-01-10"],
        ])
        conn = imp.conectar_banco()
        cursor = conn.cursor()
        inseridos, ignorados = imp.importar_arquivo(conn, cursor, caminho)
        conn.commit()
        conn.close()

        assert inseridos == 1
        assert ignorados == 0

        produto = buscar_por_nome("Vinho Legado")[0]
        assert produto.valor_unitario == pytest.approx(39.9)
        assert produto.medida_embalagem == "750ML"

        estoque = consultar_estoque_por_id(produto.id_produto)
        assert estoque.estoque_deposito == 12
        assert estoque.estoque_exposicao == 0
        assert estoque.estoque_minimo == 5

    def test_ignora_linha_vazia_e_linha_sem_nome_de_produto(self, tmp_path):
        caminho = _criar_planilha(tmp_path, [
            [None, "Produto Válido", "1UN", "UN", 1, 1, 10.0, 10.0, "OK", None],
            [None, None, None, None, None, None, None, None, None, None],
            [None, "   ", "1UN", "UN", 1, 1, 10.0, 10.0, "OK", None],
        ])
        conn = imp.conectar_banco()
        cursor = conn.cursor()
        inseridos, ignorados = imp.importar_arquivo(conn, cursor, caminho)
        conn.commit()
        conn.close()

        assert inseridos == 1
        assert ignorados == 2

    def test_produto_sem_valor_unitario_fica_com_none_nao_zero(self, tmp_path):
        """
        Regressão: 0.0 seria um preço 'de graça' de verdade, diferente de
        'sem preço cadastrado'. Tem que ficar None.
        """
        caminho = _criar_planilha(tmp_path, [
            [None, "Produto Sem Preço", "1UN", "UN", 2, 3, None, None, "OK", None],
        ])
        conn = imp.conectar_banco()
        cursor = conn.cursor()
        imp.importar_arquivo(conn, cursor, caminho)
        conn.commit()
        conn.close()

        produto = buscar_por_nome("Produto Sem Preço")[0]
        assert produto.valor_unitario is None

        relatorio = relatorio_produtos()
        ids_sem_preco = [row[0] for row in relatorio["sem_preco"]]
        assert produto.id_produto in ids_sem_preco

    def test_importacao_registra_movimento_no_historico(self, tmp_path):
        """
        Regressão: o import tem que deixar rastro em movimento_estoque,
        igual todo outro fluxo que mexe em estoque (compra, venda, ajuste).
        """
        caminho = _criar_planilha(tmp_path, [
            [None, "Vinho Legado", "750ML", "UN", 5, 12, 39.9, 478.8, "OK", None],
        ])
        conn = imp.conectar_banco()
        cursor = conn.cursor()
        imp.importar_arquivo(conn, cursor, caminho)
        conn.commit()
        conn.close()

        produto = buscar_por_nome("Vinho Legado")[0]
        movimentos = listar_movimentos(id_produto=produto.id_produto)
        assert len(movimentos) == 1
        assert movimentos[0].tipo == "IMPORTACAO_LEGADO"
        assert movimentos[0].campo == "estoque_deposito"
        assert movimentos[0].quantidade == 12

    def test_produto_com_estoque_zero_nao_gera_movimento_vazio(self, tmp_path):
        caminho = _criar_planilha(tmp_path, [
            [None, "Produto Zerado", "1UN", "UN", 1, 0, 10.0, 0.0, "OK", None],
        ])
        conn = imp.conectar_banco()
        cursor = conn.cursor()
        imp.importar_arquivo(conn, cursor, caminho)
        conn.commit()
        conn.close()

        produto = buscar_por_nome("Produto Zerado")[0]
        assert listar_movimentos(id_produto=produto.id_produto) == []


class TestImportarPastaCompleta:
    def test_importa_todos_os_arquivos_da_pasta(self, tmp_path, _pasta_planilhas_isolada):
        _criar_planilha(tmp_path / "planilhas", [
            [None, "Produto A", "1UN", "UN", 1, 5, 10.0, 50.0, "OK", None],
        ], nome_arquivo="Loja1.xlsx")
        _criar_planilha(tmp_path / "planilhas", [
            [None, "Produto B", "1UN", "UN", 1, 3, 20.0, 60.0, "OK", None],
        ], nome_arquivo="Loja2.xlsx")

        imp.importar()

        assert buscar_por_nome("Produto A")
        assert buscar_por_nome("Produto B")

    def test_ignora_arquivos_temporarios_do_excel(self, tmp_path, _pasta_planilhas_isolada):
        _criar_planilha(tmp_path / "planilhas", [
            [None, "Produto Real", "1UN", "UN", 1, 5, 10.0, 50.0, "OK", None],
        ], nome_arquivo="~$Estoque.xlsx")

        imp.importar()

        assert buscar_por_nome("Produto Real") == []  # arquivo temporário, deve ter sido ignorado

    def test_pasta_inexistente_nao_quebra(self, monkeypatch, tmp_path):
        monkeypatch.setattr(imp, "PASTA_PLANILHAS", tmp_path / "nao_existe")
        imp.importar()  # não deve levantar exceção

    def test_pasta_vazia_nao_quebra(self, _pasta_planilhas_isolada):
        imp.importar()  # não deve levantar exceção