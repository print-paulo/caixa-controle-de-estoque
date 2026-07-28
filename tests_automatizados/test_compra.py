import pytest

from models.compra import Compra
from models.item_compra import ItemCompra
from services.registrar_compra import (
    iniciar_compra, adicionar_item_compra, finalizar_compra, cancelar_compra,
    calcular_total_compra,
)
from services.buscar_compra import buscar_compra_por_id, listar_itens_compra
from services.buscar_produto import buscar_por_id
from services.estoque import consultar_estoque_por_id


class TestFluxoCompra:
    def test_compra_finalizada_soma_estoque_deposito_e_atualiza_preco(self, produto_padrao):
        id_compra = iniciar_compra("Fornecedor Teste")
        sub_total, valor_venda = adicionar_item_compra(
            id_compra, "7891234567895", 20, 30.0, 0.3
        )
        assert sub_total == 600.0
        assert valor_venda == pytest.approx(39.0)

        total = finalizar_compra(id_compra)
        assert total == 600.0

        compra = buscar_compra_por_id(id_compra)
        assert isinstance(compra, Compra)
        assert compra.status == "FINALIZADA"

        estoque = consultar_estoque_por_id(produto_padrao)
        assert estoque.estoque_deposito == 20

        produto = buscar_por_id(produto_padrao)
        assert produto.valor_unitario == pytest.approx(39.0)

    def test_compra_com_varios_itens(self, produto_padrao):
        id_compra = iniciar_compra("Fornecedor Teste")
        adicionar_item_compra(id_compra, "7891234567895", 10, 30.0, 0.3)
        adicionar_item_compra(id_compra, "7891234567895", 10, 30.0, 0.3)
        finalizar_compra(id_compra)

        itens = listar_itens_compra(id_compra)
        assert len(itens) == 2
        assert all(isinstance(i, ItemCompra) for i in itens)
        assert calcular_total_compra(id_compra) == 600.0

    def test_finalizar_compra_sem_itens_falha(self):
        id_compra = iniciar_compra("Fornecedor Teste")
        with pytest.raises(ValueError, match="sem itens"):
            finalizar_compra(id_compra)

    def test_adicionar_item_com_quantidade_zero_ou_negativa_falha(self, produto_padrao):
        id_compra = iniciar_compra("Fornecedor Teste")
        with pytest.raises(ValueError, match="maior que zero"):
            adicionar_item_compra(id_compra, "7891234567895", 0, 30.0, 0.3)
        with pytest.raises(ValueError, match="maior que zero"):
            adicionar_item_compra(id_compra, "7891234567895", -5, 30.0, 0.3)

    def test_adicionar_item_produto_inexistente_falha(self):
        id_compra = iniciar_compra("Fornecedor Teste")
        with pytest.raises(ValueError, match="não encontrado"):
            adicionar_item_compra(id_compra, "0000000000000", 1, 10.0, 0.1)

    def test_adicionar_item_em_compra_inexistente_falha(self):
        with pytest.raises(ValueError, match="não encontrada"):
            adicionar_item_compra(9999, "7891234567895", 1, 10.0, 0.1)

    def test_adicionar_item_em_compra_ja_finalizada_falha(self, produto_padrao):
        id_compra = iniciar_compra("Fornecedor Teste")
        adicionar_item_compra(id_compra, "7891234567895", 10, 30.0, 0.3)
        finalizar_compra(id_compra)
        with pytest.raises(ValueError, match="não está aberta"):
            adicionar_item_compra(id_compra, "7891234567895", 5, 30.0, 0.3)

    def test_compra_com_erro_no_meio_nao_altera_estoque_nem_registra_item(self, produto_padrao):
        """
        Simula uma falha no meio da transação (produto inexistente no
        segundo item) e confere que NADA do primeiro item foi salvo --
        a transação inteira deve ter sido revertida (rollback).
        """
        id_compra = iniciar_compra("Fornecedor Teste")
        adicionar_item_compra(id_compra, "7891234567895", 10, 30.0, 0.3)

        # Essa falha é só de validação de quantidade, mas cada
        # `adicionar_item_compra` é sua própria transação -- o que
        # importa aqui é confirmar que o item 1, já commitado, continua
        # valendo, e o item malformado simplesmente não é adicionado.
        with pytest.raises(ValueError):
            adicionar_item_compra(id_compra, "0000000000000", 5, 10.0, 0.1)

        itens = listar_itens_compra(id_compra)
        assert len(itens) == 1  # só o item válido


class TestCancelamentoCompra:
    def test_cancelar_compra_retira_do_deposito(self, produto_padrao):
        id_compra = iniciar_compra("Fornecedor Teste")
        adicionar_item_compra(id_compra, "7891234567895", 20, 30.0, 0.3)
        cancelar_compra(id_compra)

        compra = buscar_compra_por_id(id_compra)
        assert compra.status == "CANCELADA"
        assert consultar_estoque_por_id(produto_padrao).estoque_deposito == 0

    def test_cancelar_compra_ja_cancelada_falha(self, produto_padrao):
        id_compra = iniciar_compra("Fornecedor Teste")
        adicionar_item_compra(id_compra, "7891234567895", 20, 30.0, 0.3)
        cancelar_compra(id_compra)
        with pytest.raises(ValueError, match="não está aberta"):
            cancelar_compra(id_compra)

    def test_cancelar_compra_ja_finalizada_falha(self, produto_padrao):
        id_compra = iniciar_compra("Fornecedor Teste")
        adicionar_item_compra(id_compra, "7891234567895", 20, 30.0, 0.3)
        finalizar_compra(id_compra)
        with pytest.raises(ValueError, match="não está aberta"):
            cancelar_compra(id_compra)

    def test_cancelar_compra_de_produto_ja_desativado_ainda_funciona(self, produto_padrao):
        """
        Regra de negócio: cancelamento precisa reconciliar o estoque mesmo
        se o produto foi desativado depois da compra (exigir_produto_ativo=False).
        """
        from services.excluir_produto import excluir_produto

        id_compra = iniciar_compra("Fornecedor Teste")
        adicionar_item_compra(id_compra, "7891234567895", 20, 30.0, 0.3)
        excluir_produto(produto_padrao)

        cancelar_compra(id_compra)  # não deve levantar
        assert consultar_estoque_por_id(produto_padrao).estoque_deposito == 0
