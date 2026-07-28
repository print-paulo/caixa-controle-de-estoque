import pytest

from models.estoque import Estoque
from models.movimento_estoque import MovimentoEstoque
from services.registrar_compra import iniciar_compra, adicionar_item_compra, finalizar_compra
from services.estoque import (
    consultar_estoque_por_id, listar_estoque_completo, listar_produtos_abaixo_minimo,
    repor_exposicao, ajustar_estoque_deposito, ajustar_estoque_exposicao,
    ajustar_estoque_minimo, ajustar_capacidade_exposicao, listar_movimentos,
)


def _comprar(produto_id, quantidade, custo=30.0, margem=0.3, codigo="7891234567895"):
    id_compra = iniciar_compra("Fornecedor Teste")
    adicionar_item_compra(id_compra, codigo, quantidade, custo, margem)
    finalizar_compra(id_compra)


class TestConsulta:
    def test_consultar_estoque_por_id_produto_novo(self, produto_padrao):
        estoque = consultar_estoque_por_id(produto_padrao)
        assert isinstance(estoque, Estoque)
        assert estoque.estoque_deposito == 0
        assert estoque.estoque_exposicao == 0
        assert estoque.nome_produto == "Vinho Tinto Reserva"

    def test_consultar_estoque_produto_inexistente_devolve_none(self):
        assert consultar_estoque_por_id(9999) is None

    def test_listar_estoque_completo_ignora_produto_inativo(self, produto_padrao):
        from services.excluir_produto import excluir_produto
        from services.cadastrar_produto import cadastrar_produto_completo

        cadastrar_produto_completo(nome_produto="Outro Ativo")
        excluir_produto(produto_padrao)

        lista = listar_estoque_completo()
        assert all(isinstance(e, Estoque) for e in lista)
        nomes = {e.nome_produto for e in lista}
        assert "Vinho Tinto Reserva" not in nomes
        assert "Outro Ativo" in nomes

    def test_listar_produtos_abaixo_minimo(self, produto_padrao):
        # estoque_minimo do produto_padrao é 3; sem nenhuma compra, depósito=0 <= 3
        abaixo = listar_produtos_abaixo_minimo()
        assert len(abaixo) == 1

        _comprar(produto_padrao, 50)  # bem acima do mínimo
        abaixo_depois = listar_produtos_abaixo_minimo()
        assert len(abaixo_depois) == 0


class TestReposicaoManual:
    def test_repor_exposicao_quantidade_automatica_ate_capacidade(self, produto_padrao):
        _comprar(produto_padrao, 3)  # capacidade de exposição do produto_padrao é 10
        movido = repor_exposicao(produto_padrao)  # sem quantidade -> repõe o máximo possível
        assert movido == 3  # só tinha 3 no depósito

        estoque = consultar_estoque_por_id(produto_padrao)
        assert estoque.estoque_deposito == 0
        assert estoque.estoque_exposicao == 3

    def test_repor_exposicao_quantidade_especifica(self, produto_padrao):
        _comprar(produto_padrao, 20)
        movido = repor_exposicao(produto_padrao, quantidade=5)
        assert movido == 5
        assert consultar_estoque_por_id(produto_padrao).estoque_exposicao == 5

    def test_repor_exposicao_alem_do_deposito_falha(self, produto_padrao):
        _comprar(produto_padrao, 2)
        with pytest.raises(ValueError, match="não tem"):
            repor_exposicao(produto_padrao, quantidade=100)

    def test_repor_exposicao_alem_da_capacidade_falha(self, produto_padrao):
        _comprar(produto_padrao, 50)  # capacidade é 10
        with pytest.raises(ValueError, match="ultrapassaria"):
            repor_exposicao(produto_padrao, quantidade=50)


class TestAjusteManual:
    def test_ajustar_estoque_deposito_soma_delta_e_retorna_novo_valor(self, produto_padrao):
        novo_valor = ajustar_estoque_deposito(produto_padrao, 10)
        assert novo_valor == 10
        assert consultar_estoque_por_id(produto_padrao).estoque_deposito == 10

    def test_ajustar_aceita_delta_negativo(self, produto_padrao):
        ajustar_estoque_deposito(produto_padrao, 10)
        novo_valor = ajustar_estoque_deposito(produto_padrao, -4)
        assert novo_valor == 6

    def test_ajuste_que_resultaria_em_negativo_falha_e_nao_altera_nada(self, produto_padrao):
        ajustar_estoque_deposito(produto_padrao, 5)
        with pytest.raises(ValueError, match="negativo"):
            ajustar_estoque_deposito(produto_padrao, -10)
        assert consultar_estoque_por_id(produto_padrao).estoque_deposito == 5

    def test_ajustar_estoque_de_produto_inativo_falha_por_padrao(self, produto_padrao):
        from services.excluir_produto import excluir_produto
        excluir_produto(produto_padrao)
        with pytest.raises(ValueError, match="não encontrado ou inativo"):
            ajustar_estoque_deposito(produto_padrao, 10)

    def test_ajustar_minimo_e_capacidade(self, produto_padrao):
        assert ajustar_estoque_minimo(produto_padrao, 2) == 5
        assert ajustar_capacidade_exposicao(produto_padrao, -1) == 9
        assert ajustar_estoque_exposicao(produto_padrao, 4) == 4


class TestHistoricoMovimentos:
    def test_cada_ajuste_gera_um_movimento_do_tipo_ajuste(self, produto_padrao):
        ajustar_estoque_deposito(produto_padrao, 10)
        movimentos = listar_movimentos(id_produto=produto_padrao, tipo="AJUSTE")
        assert len(movimentos) == 1
        assert isinstance(movimentos[0], MovimentoEstoque)
        assert movimentos[0].quantidade == 10
        assert movimentos[0].campo == "estoque_deposito"

    def test_compra_gera_movimento_tipo_compra(self, produto_padrao):
        _comprar(produto_padrao, 15)
        movimentos = listar_movimentos(id_produto=produto_padrao, tipo="COMPRA")
        assert len(movimentos) == 1
        assert movimentos[0].quantidade == 15

    def test_listar_movimentos_sem_filtro_traz_todos_os_produtos(self, produto_padrao):
        from services.cadastrar_produto import cadastrar_produto_completo

        id_produto2 = cadastrar_produto_completo(
            nome_produto="Cerveja", codigo_barras="222", capacidade_exposicao=5, estoque_minimo=1,
        )
        ajustar_estoque_deposito(produto_padrao, 5)
        ajustar_estoque_deposito(id_produto2, 3)

        todos = listar_movimentos()
        assert len(todos) == 2
        assert all(isinstance(m, MovimentoEstoque) for m in todos)

    def test_listar_movimentos_respeita_limite(self, produto_padrao):
        for i in range(5):
            ajustar_estoque_minimo(produto_padrao, 1)
        limitados = listar_movimentos(id_produto=produto_padrao, limite=2)
        assert len(limitados) == 2

    def test_movimentos_mais_recente_primeiro(self, produto_padrao):
        ajustar_estoque_deposito(produto_padrao, 1)
        ajustar_estoque_deposito(produto_padrao, 2)
        ajustar_estoque_deposito(produto_padrao, 3)
        movimentos = listar_movimentos(id_produto=produto_padrao)
        quantidades_na_ordem = [m.quantidade for m in movimentos]
        assert quantidades_na_ordem == [3, 2, 1]
