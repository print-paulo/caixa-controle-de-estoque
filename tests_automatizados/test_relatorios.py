import pytest

from services.cadastrar_produto import cadastrar_produto_completo
from services.excluir_produto import excluir_produto
from services.registrar_compra import iniciar_compra, adicionar_item_compra, finalizar_compra
from services.registrar_venda import iniciar_venda, adicionar_item_venda, finalizar_venda
from services.relatorios import (
    relatorio_produtos, relatorio_estoque, relatorio_vendas,
    relatorio_compras, relatorio_lucro,
)


class TestRelatorioProdutos:
    def test_conta_ativos_e_inativos(self, produto_padrao):
        cadastrar_produto_completo(nome_produto="Outro Ativo")
        inativo_id = cadastrar_produto_completo(nome_produto="Vai Ser Excluído")
        excluir_produto(inativo_id)

        relatorio = relatorio_produtos()
        assert relatorio["total_ativos"] == 2
        assert relatorio["total_inativos"] == 1

    def test_agrupa_por_categoria(self, produto_padrao):
        cadastrar_produto_completo(nome_produto="Cerveja X", nome_categoria="Cervejas")
        relatorio = relatorio_produtos()
        categorias = dict(relatorio["por_categoria"])
        assert categorias["Vinhos"] == 1
        assert categorias["Cervejas"] == 1

    def test_lista_produtos_sem_preco(self, produto_padrao):
        # produto_padrao nunca passou por compra -> sem valor_unitario
        relatorio = relatorio_produtos()
        ids_sem_preco = [row[0] for row in relatorio["sem_preco"]]
        assert produto_padrao in ids_sem_preco


class TestRelatorioEstoque:
    def test_valor_total_e_quantidade_apos_compra(self, produto_padrao):
        id_compra = iniciar_compra("Forn")
        adicionar_item_compra(id_compra, "7891234567895", 10, 30.0, 0.3)
        finalizar_compra(id_compra)

        relatorio = relatorio_estoque()
        assert relatorio["quantidade_total_unidades"] == 10
        assert relatorio["valor_total_estoque"] == pytest.approx(10 * 39.0)

    def test_produtos_abaixo_minimo_sem_nenhuma_compra(self, produto_padrao):
        relatorio = relatorio_estoque()
        assert relatorio["produtos_abaixo_minimo"] == 1  # estoque_minimo=3, depósito=0


class TestRelatorioVendas:
    def test_soma_apenas_vendas_finalizadas(self, produto_padrao):
        id_compra = iniciar_compra("Forn")
        adicionar_item_compra(id_compra, "7891234567895", 20, 30.0, 0.3)
        finalizar_compra(id_compra)

        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)
        finalizar_venda(id_venda, "PIX")

        # venda em aberto, não deve contar
        iniciar_venda()

        relatorio = relatorio_vendas()
        assert relatorio["quantidade_vendas"] == 1
        assert relatorio["total_vendido"] == pytest.approx(3 * 39.0)
        assert relatorio["ticket_medio"] == pytest.approx(3 * 39.0)

    def test_sem_vendas_devolve_zeros_sem_dividir_por_zero(self):
        relatorio = relatorio_vendas()
        assert relatorio["quantidade_vendas"] == 0
        assert relatorio["total_vendido"] == 0
        assert relatorio["ticket_medio"] == 0.0


class TestRelatorioLucro:
    def test_lucro_bruto_e_a_diferenca_entre_vendido_e_investido(self, produto_padrao):
        id_compra = iniciar_compra("Forn")
        adicionar_item_compra(id_compra, "7891234567895", 20, 30.0, 0.3)  # investe 600
        finalizar_compra(id_compra)

        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)  # vende 3 * 39 = 117
        finalizar_venda(id_venda, "PIX")

        relatorio = relatorio_lucro()
        assert relatorio["total_investido"] == 600.0
        assert relatorio["total_vendido"] == pytest.approx(117.0)
        assert relatorio["lucro_bruto"] == pytest.approx(117.0 - 600.0)

    def test_sem_movimento_nenhum_lucro_e_zero(self):
        relatorio = relatorio_lucro()
        assert relatorio == {
            "total_vendido": 0,
            "total_investido": 0,
            "lucro_bruto": 0,
            "lucro_real": 0,
            "unidades_sem_custo_registrado": 0,
        }