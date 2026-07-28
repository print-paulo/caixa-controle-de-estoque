import pytest

from models.venda import Venda
from models.item_venda import ItemVenda
from services.registrar_compra import iniciar_compra, adicionar_item_compra, finalizar_compra
from services.registrar_venda import (
    iniciar_venda, adicionar_item_venda, finalizar_venda, cancelar_venda,
    calcular_total_venda,
)
from services.buscar_venda import buscar_venda_por_id, listar_itens_venda
from services.estoque import consultar_estoque_por_id


def _comprar(produto_id, quantidade, custo=30.0, margem=0.3, codigo="7891234567895"):
    """Helper: registra e finaliza uma compra pra abastecer o depósito antes da venda."""
    id_compra = iniciar_compra("Fornecedor Teste")
    adicionar_item_compra(id_compra, codigo, quantidade, custo, margem)
    finalizar_compra(id_compra)
    return id_compra


class TestFluxoVenda:
    def test_venda_finalizada_desconta_exposicao_e_calcula_total(self, produto_padrao):
        _comprar(produto_padrao, 20)  # repõe exposição automaticamente até a capacidade (10)

        id_venda = iniciar_venda()
        resultado = adicionar_item_venda(id_venda, "7891234567895", 3)
        assert resultado["subtotal"] == pytest.approx(3 * 39.0)

        total = finalizar_venda(id_venda, "DINHEIRO")
        assert total == pytest.approx(3 * 39.0)

        venda = buscar_venda_por_id(id_venda)
        assert isinstance(venda, Venda)
        assert venda.status == "FINALIZADA"
        assert venda.forma_pagamento == "DINHEIRO"

        estoque = consultar_estoque_por_id(produto_padrao)
        assert estoque.estoque_exposicao == 7  # repôs 10, vendeu 3
        assert estoque.estoque_deposito == 10  # 20 comprados - 10 repostos

    def test_reposicao_automatica_move_do_deposito_pra_exposicao(self, produto_padrao):
        _comprar(produto_padrao, 5)  # menos que a capacidade de exposição (10)

        id_venda = iniciar_venda()
        resultado = adicionar_item_venda(id_venda, "7891234567895", 2)
        assert resultado["quantidade_reposta"] == 5  # tudo que tinha no depósito

        estoque = consultar_estoque_por_id(produto_padrao)
        assert estoque.estoque_deposito == 0
        assert estoque.estoque_exposicao == 3  # repôs 5, vendeu 2

    def test_venda_com_estoque_insuficiente_falha_e_nao_altera_nada(self, produto_padrao):
        _comprar(produto_padrao, 2)  # só no depósito, exposição continua 0

        id_venda = iniciar_venda()
        with pytest.raises(ValueError, match="Estoque insuficiente"):
            adicionar_item_venda(id_venda, "7891234567895", 100)

        # rollback: mesmo a reposição automática que rodou ANTES da
        # validação de estoque (e chegou a imprimir a mensagem) precisa
        # ser desfeita por inteiro, já que tudo está na mesma transação
        estoque = consultar_estoque_por_id(produto_padrao)
        assert estoque.estoque_deposito == 2
        assert estoque.estoque_exposicao == 0

    def test_alerta_de_estoque_minimo_no_retorno(self, produto_padrao):
        _comprar(produto_padrao, 10)  # estoque_minimo do produto_padrao é 3

        id_venda = iniciar_venda()
        # depois da reposição automática, depósito fica em 0 (repôs os 10 pra exposição)
        resultado = adicionar_item_venda(id_venda, "7891234567895", 1)
        assert resultado["estoque_baixo"] is True  # depósito (0) <= mínimo (3)

    def test_venda_de_produto_sem_preco_falha(self):
        """
        Um produto só ganha `valor_unitario` através de uma compra. Se o
        estoque de exposição for alimentado por outro caminho (ajuste
        manual, sem nunca passar por uma compra), a venda deve recusar
        com uma mensagem clara em vez de vender por None/0.
        """
        from services.cadastrar_produto import cadastrar_produto_completo
        from services.estoque import ajustar_estoque_exposicao

        id_produto = cadastrar_produto_completo(nome_produto="Sem Preço", codigo_barras="999888777")
        ajustar_estoque_exposicao(id_produto, 5)  # estoque manual, sem nunca ter passado por compra

        id_venda = iniciar_venda()
        with pytest.raises(ValueError, match="não possui preço cadastrado"):
            adicionar_item_venda(id_venda, "999888777", 1)

    def test_finalizar_venda_sem_itens_falha(self):
        id_venda = iniciar_venda()
        with pytest.raises(ValueError, match="sem itens"):
            finalizar_venda(id_venda, "DINHEIRO")

    def test_finalizar_venda_sem_forma_pagamento_falha(self, produto_padrao):
        _comprar(produto_padrao, 10)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 1)
        with pytest.raises(ValueError, match="não pode ser vazia"):
            finalizar_venda(id_venda, "   ")

    def test_adicionar_item_quantidade_invalida_falha(self, produto_padrao):
        _comprar(produto_padrao, 10)
        id_venda = iniciar_venda()
        with pytest.raises(ValueError, match="maior que zero"):
            adicionar_item_venda(id_venda, "7891234567895", 0)

    def test_adicionar_item_em_venda_ja_finalizada_falha(self, produto_padrao):
        _comprar(produto_padrao, 10)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 1)
        finalizar_venda(id_venda, "PIX")
        with pytest.raises(ValueError, match="não está aberta"):
            adicionar_item_venda(id_venda, "7891234567895", 1)

    def test_venda_com_varios_itens(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 2)
        adicionar_item_venda(id_venda, "7891234567895", 1)
        finalizar_venda(id_venda, "DINHEIRO")

        itens = listar_itens_venda(id_venda)
        assert len(itens) == 2
        assert all(isinstance(i, ItemVenda) for i in itens)
        assert calcular_total_venda(id_venda) == pytest.approx(3 * 39.0)


class TestCancelamentoVenda:
    def test_cancelar_venda_devolve_estoque_de_exposicao(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)
        estoque_antes = consultar_estoque_por_id(produto_padrao).estoque_exposicao

        cancelar_venda(id_venda)

        venda = buscar_venda_por_id(id_venda)
        assert venda.status == "CANCELADA"
        estoque_depois = consultar_estoque_por_id(produto_padrao).estoque_exposicao
        assert estoque_depois == estoque_antes + 3

    def test_cancelar_venda_ja_cancelada_falha(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)
        cancelar_venda(id_venda)
        with pytest.raises(ValueError, match="não está aberta"):
            cancelar_venda(id_venda)

    def test_cancelar_venda_ja_finalizada_falha(self, produto_padrao):
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)
        finalizar_venda(id_venda, "DINHEIRO")
        with pytest.raises(ValueError, match="não está aberta"):
            cancelar_venda(id_venda)

    def test_cancelar_venda_de_produto_ja_desativado_ainda_funciona(self, produto_padrao):
        from services.excluir_produto import excluir_produto

        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)
        excluir_produto(produto_padrao)

        cancelar_venda(id_venda)  # não deve levantar
        assert buscar_venda_por_id(id_venda).status == "CANCELADA"

    def test_nao_e_possivel_cancelar_a_mesma_venda_duas_vezes_descontando_estoque_errado(self, produto_padrao):
        """
        Regressão do bug documentado no histórico do projeto: cancelar a
        mesma venda duas vezes não pode devolver o estoque em dobro.
        """
        _comprar(produto_padrao, 20)
        id_venda = iniciar_venda()
        adicionar_item_venda(id_venda, "7891234567895", 3)
        cancelar_venda(id_venda)
        estoque_depois_1_cancelamento = consultar_estoque_por_id(produto_padrao).estoque_exposicao

        with pytest.raises(ValueError):
            cancelar_venda(id_venda)

        estoque_depois_2_tentativa = consultar_estoque_por_id(produto_padrao).estoque_exposicao
        assert estoque_depois_1_cancelamento == estoque_depois_2_tentativa
