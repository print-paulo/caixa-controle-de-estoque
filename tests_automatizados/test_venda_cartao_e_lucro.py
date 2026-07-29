import pytest

from services.registrar_venda import (
    iniciar_venda, adicionar_item_venda, finalizar_venda,
    eh_pagamento_no_cartao, taxa_cartao, TAXA_CARTAO_DEBITO, TAXA_CARTAO_CREDITO,
)
from services.registrar_compra import iniciar_compra, adicionar_item_compra, finalizar_compra
from services.buscar_venda import buscar_venda_por_id, listar_itens_venda
from services.buscar_produto import buscar_por_id
from services.relatorios import relatorio_compras, relatorio_lucro, relatorio_vendas


def _comprar(produto_id, quantidade, custo=30.0, margem=0.3, codigo="7891234567895"):
    id_compra = iniciar_compra("Fornecedor Teste")
    adicionar_item_compra(id_compra, codigo, quantidade, custo, margem)
    finalizar_compra(id_compra)
    return id_compra


class TestEhPagamentoNoCartao:
    @pytest.mark.parametrize("forma", [
        "cartao", "Cartão", "CARTÃO", "cartão de crédito", "cartao debito", "no cartao", "débito", "crédito",
    ])
    def test_reconhece_variacoes_de_cartao_debito_ou_credito(self, forma):
        assert eh_pagamento_no_cartao(forma) is True

    @pytest.mark.parametrize("forma", ["DINHEIRO", "PIX", "dinheiro", "boleto"])
    def test_nao_reconhece_outras_formas(self, forma):
        assert eh_pagamento_no_cartao(forma) is False


class TestTaxaCartao:
    @pytest.mark.parametrize("forma", ["debito", "Débito", "cartão débito", "cartao de debito"])
    def test_reconhece_debito(self, forma):
        assert taxa_cartao(forma) == TAXA_CARTAO_DEBITO

    @pytest.mark.parametrize("forma", ["credito", "Crédito", "cartão crédito", "cartao de credito"])
    def test_reconhece_credito(self, forma):
        assert taxa_cartao(forma) == TAXA_CARTAO_CREDITO

    def test_cartao_sem_especificar_debito_ou_credito_e_ambiguo(self):
        with pytest.raises(ValueError, match="ambígua"):
            taxa_cartao("cartao")

    @pytest.mark.parametrize("forma", ["DINHEIRO", "PIX", "boleto"])
    def test_formas_sem_cartao_nao_tem_taxa(self, forma):
        assert taxa_cartao(forma) == 0.0


class TestTaxaDeCartaoNaFinalizacao:
    def test_pagamento_em_dinheiro_nao_tem_taxa(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)  # subtotal = 3 * 39 = 117
        total = finalizar_venda(id_venda, "DINHEIRO")
        assert total == pytest.approx(117.0)
        assert buscar_venda_por_id(id_venda).valor_total == pytest.approx(117.0)

    def test_pagamento_no_credito_aplica_taxa_de_5_por_cento(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)  # subtotal = 117
        total = finalizar_venda(id_venda, "Cartão de Crédito")
        esperado = round(117.0 * (1 + TAXA_CARTAO_CREDITO), 2)
        assert total == pytest.approx(esperado)
        assert buscar_venda_por_id(id_venda).valor_total == pytest.approx(esperado)

    def test_pagamento_no_debito_aplica_taxa_de_3_por_cento(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)  # subtotal = 117
        total = finalizar_venda(id_venda, "Cartão de Débito")
        esperado = round(117.0 * (1 + TAXA_CARTAO_DEBITO), 2)
        assert total == pytest.approx(esperado)
        assert buscar_venda_por_id(id_venda).valor_total == pytest.approx(esperado)

    def test_debito_e_credito_geram_totais_diferentes(self, produto_padrao):
        _comprar(produto_padrao, 20)

        id_venda_debito = iniciar_venda()
        adicionar_item_venda(id_venda_debito, "7891234567895", 1)  # subtotal = 39
        total_debito = finalizar_venda(id_venda_debito, "debito")

        id_venda_credito = iniciar_venda()
        adicionar_item_venda(id_venda_credito, "7891234567895", 1)  # subtotal = 39
        total_credito = finalizar_venda(id_venda_credito, "credito")

        assert total_credito > total_debito

    def test_finalizar_com_cartao_ambiguo_falha_e_nao_finaliza_a_venda(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 1)

        with pytest.raises(ValueError, match="ambígua"):
            finalizar_venda(id_venda, "cartao")

        venda = buscar_venda_por_id(id_venda)
        assert venda.status == "ABERTA"  # não deve ter sido finalizada
        assert venda.valor_total is None

    def test_taxa_de_cartao_e_insensivel_a_acento_e_caixa(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 1)  # subtotal = 39
        total = finalizar_venda(id_venda, "CREDITO")
        assert total == pytest.approx(round(39.0 * (1 + TAXA_CARTAO_CREDITO), 2))

    def test_venda_recem_criada_tem_valor_total_none(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 1)
        assert buscar_venda_por_id(id_venda).valor_total is None  # só é definido ao finalizar


class TestCustoUnitarioPropagado:
    def test_compra_atualiza_custo_unitario_do_produto(self, produto_padrao):
        _comprar(produto_padrao, 10, custo=25.0, margem=0.5)
        produto = buscar_por_id(produto_padrao)
        assert produto.custo_unitario == pytest.approx(25.0)
        assert produto.valor_unitario == pytest.approx(25.0 * 1.5)

    def test_venda_congela_custo_unitario_no_item_venda(self, produto_padrao):
        _comprar(produto_padrao, 10, custo=25.0, margem=0.5)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 2)
        finalizar_venda(id_venda, "DINHEIRO")

        item = listar_itens_venda(id_venda)[0]
        assert item.custo_unitario_momento == pytest.approx(25.0)
        assert item.valor_unitario_momento == pytest.approx(37.5)

    def test_item_venda_de_produto_sem_custo_registrado_fica_com_custo_none(self, produto_padrao):
        """
        Se o estoque de exposição for alimentado sem nunca ter passado por
        uma compra (ajuste manual), o produto não tem custo_unitario -- o
        item de venda deve refletir isso com None, não quebrar.
        """
        from services.cadastrar_produto import cadastrar_produto_completo
        from services.estoque import ajustar_estoque_exposicao
        from utils.db_campos import atualizar_campo_produto

        id_produto = cadastrar_produto_completo(nome_produto="Produto Manual", codigo_barras="55555")
        atualizar_campo_produto(id_produto, "valor_unitario", 10.0)  # preço sem custo definido
        ajustar_estoque_exposicao(id_produto, 5)

        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "55555", 1)
        finalizar_venda(id_venda, "DINHEIRO")

        item = listar_itens_venda(id_venda)[0]
        assert item.custo_unitario_momento is None


class TestLucroEsperadoNaCompra:
    def test_lucro_esperado_total_soma_margem_de_todos_os_itens_comprados(self, produto_padrao):
        id_compra = iniciar_compra("Forn")
        adicionar_item_compra(id_compra, "7891234567895", 10, 30.0, 0.3)  # margem 9/unid * 10 = 90
        finalizar_compra(id_compra)

        relatorio = relatorio_compras()
        assert relatorio["lucro_esperado_total"] == pytest.approx(90.0)


class TestLucroReal:
    def test_lucro_real_usa_custo_congelado_no_momento_da_venda(self, produto_padrao):
        _comprar(produto_padrao, 20, custo=30.0, margem=0.3)  # preço de venda = 39

        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)  # margem 9/unid * 3 = 27
        finalizar_venda(id_venda, "DINHEIRO")

        relatorio = relatorio_lucro()
        assert relatorio["lucro_real"] == pytest.approx(27.0)
        assert relatorio["unidades_sem_custo_registrado"] == 0

    def test_lucro_real_ignora_mas_conta_unidades_sem_custo_registrado(self, produto_padrao):
        from services.cadastrar_produto import cadastrar_produto_completo
        from services.estoque import ajustar_estoque_exposicao
        from utils.db_campos import atualizar_campo_produto

        id_produto = cadastrar_produto_completo(nome_produto="Produto Manual", codigo_barras="55555")
        atualizar_campo_produto(id_produto, "valor_unitario", 10.0)
        ajustar_estoque_exposicao(id_produto, 5)

        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "55555", 2)
        finalizar_venda(id_venda, "DINHEIRO")

        relatorio = relatorio_lucro()
        assert relatorio["lucro_real"] == 0  # ignorado, sem custo pra calcular margem
        assert relatorio["unidades_sem_custo_registrado"] == 2

    def test_lucro_real_nao_conta_venda_de_outro_produto_com_custo(self, produto_padrao):
        """Mistura um produto COM custo e um SEM custo na mesma venda/período."""
        from services.cadastrar_produto import cadastrar_produto_completo
        from services.estoque import ajustar_estoque_exposicao
        from utils.db_campos import atualizar_campo_produto

        _comprar(produto_padrao, 20, custo=30.0, margem=0.3)  # margem 9/unid

        id_sem_custo = cadastrar_produto_completo(nome_produto="Sem Custo", codigo_barras="777")
        atualizar_campo_produto(id_sem_custo, "valor_unitario", 5.0)
        ajustar_estoque_exposicao(id_sem_custo, 5)

        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 2)  # margem real: 9*2=18
        adicionar_item_venda(id_venda, "777", 3)  # sem custo
        finalizar_venda(id_venda, "DINHEIRO")

        relatorio = relatorio_lucro()
        assert relatorio["lucro_real"] == pytest.approx(18.0)
        assert relatorio["unidades_sem_custo_registrado"] == 3

    def test_lucro_bruto_e_lucro_real_podem_divergir_quando_compra_supera_venda_do_periodo(self, produto_padrao):
        """
        Documenta a diferença entre as duas métricas: compra um lote grande
        (sai caro no regime de caixa) e vende só uma fração -- lucro_bruto
        fica negativo (parece prejuízo), mas lucro_real reflete que cada
        unidade vendida realmente deu lucro.
        """
        _comprar(produto_padrao, 100, custo=30.0, margem=0.3)  # investe 3000

        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 2)  # vende só 2 (2*39=78)
        finalizar_venda(id_venda, "DINHEIRO")

        relatorio = relatorio_lucro()
        assert relatorio["lucro_bruto"] < 0  # 78 - 3000
        assert relatorio["lucro_real"] == pytest.approx(18.0)  # 9 de margem * 2 unidades