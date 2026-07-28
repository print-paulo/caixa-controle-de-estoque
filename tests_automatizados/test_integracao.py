"""
Teste de integração: replica o fluxo funcional completo que o projeto usa
como critério de revisão manual (cadastro -> compra -> venda -> estoque ->
relatório), só que automatizado.
"""
from services.cadastrar_produto import cadastrar_produto_completo
from services.buscar_produto import buscar_por_id
from services.registrar_compra import iniciar_compra, adicionar_item_compra, finalizar_compra
from services.registrar_venda import iniciar_venda, adicionar_item_venda, finalizar_venda, cancelar_venda
from services.buscar_venda import buscar_venda_por_id, listar_itens_venda
from services.estoque import consultar_estoque_por_id, listar_movimentos
from services.relatorios import relatorio_lucro
from models.produto import Produto
from models.venda import Venda
from models.item_venda import ItemVenda
from models.estoque import Estoque
from models.movimento_estoque import MovimentoEstoque


def test_fluxo_completo_cadastro_compra_venda_estoque_relatorio():
    # cadastro
    id_produto = cadastrar_produto_completo(
        nome_produto="Vinho Tinto Reserva",
        nome_categoria="Vinhos",
        codigo_barras="7891234567895",
        medida_embalagem="750ML",
        unidade="UN",
        capacidade_exposicao=10,
        estoque_minimo=3,
    )
    assert isinstance(buscar_por_id(id_produto), Produto)

    # compra (reposição automática só acontece na VENDA, não na compra --
    # aqui tudo vai pro depósito)
    id_compra = iniciar_compra("Fornecedor Teste")
    adicionar_item_compra(id_compra, "7891234567895", 20, 30.0, 0.3)
    finalizar_compra(id_compra)
    assert consultar_estoque_por_id(id_produto).estoque_deposito == 20
    assert consultar_estoque_por_id(id_produto).estoque_exposicao == 0

    # venda (com reposição automática já esgotada pela compra)
    id_venda = iniciar_venda()
    adicionar_item_venda(id_venda, "7891234567895", 3)
    finalizar_venda(id_venda, "DINHEIRO")

    venda = buscar_venda_por_id(id_venda)
    assert isinstance(venda, Venda)
    assert venda.status == "FINALIZADA"

    itens = listar_itens_venda(id_venda)
    assert isinstance(itens[0], ItemVenda)
    assert itens[0].quantidade == 3

    # estoque refletindo a venda
    estoque = consultar_estoque_por_id(id_produto)
    assert isinstance(estoque, Estoque)
    assert estoque.estoque_exposicao == 7

    # histórico de movimentação com todos os tipos esperados até aqui
    movimentos = listar_movimentos(id_produto=id_produto)
    assert all(isinstance(m, MovimentoEstoque) for m in movimentos)
    tipos = {m.tipo for m in movimentos}
    assert tipos == {"COMPRA", "REPOSICAO", "VENDA"}

    # cancelamento
    id_venda2 = iniciar_venda()
    adicionar_item_venda(id_venda2, "7891234567895", 2)
    cancelar_venda(id_venda2)
    assert buscar_venda_por_id(id_venda2).status == "CANCELADA"

    # relatório
    relatorio = relatorio_lucro()
    assert relatorio["total_investido"] == 600.0
    assert relatorio["total_vendido"] > 0
