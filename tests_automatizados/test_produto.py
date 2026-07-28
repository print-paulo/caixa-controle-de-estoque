import pytest

from models.produto import Produto
from services.cadastrar_produto import cadastrar_produto_completo
from services.buscar_produto import (
    buscar_por_codigo_barras, buscar_por_nome, buscar_por_id, listar_todos,
)
from services.editar_produto import (
    editar_nome_produto, editar_valor_unitario, editar_codigo_barras,
)
from services.excluir_produto import excluir_produto, reativar_produto
from utils.db_campos import atualizar_campo_estoque


class TestCadastro:
    def test_cadastra_produto_completo_e_devolve_id(self):
        id_produto = cadastrar_produto_completo(
            nome_produto="Vinho Tinto Reserva",
            nome_categoria="Vinhos",
            codigo_barras="7891234567895",
            medida_embalagem="750ML",
            unidade="UN",
            capacidade_exposicao=10,
            estoque_minimo=3,
        )
        assert id_produto is not None

        produto = buscar_por_id(id_produto)
        assert isinstance(produto, Produto)
        assert produto.nome_produto == "Vinho Tinto Reserva"
        assert produto.ativo is True

    def test_rejeita_nome_vazio(self):
        with pytest.raises(ValueError, match="Nome do produto não pode ser vazio"):
            cadastrar_produto_completo(nome_produto="   ")

    def test_rejeita_capacidade_negativa(self):
        with pytest.raises(ValueError, match="não pode ser negativa"):
            cadastrar_produto_completo(nome_produto="Produto X", capacidade_exposicao=-1)

    def test_rejeita_estoque_minimo_negativo(self):
        with pytest.raises(ValueError, match="não pode ser negativo"):
            cadastrar_produto_completo(nome_produto="Produto X", estoque_minimo=-1)

    def test_rejeita_codigo_de_barras_duplicado_em_produto_ativo(self):
        cadastrar_produto_completo(nome_produto="Produto A", codigo_barras="123")
        with pytest.raises(ValueError, match="já está cadastrado"):
            cadastrar_produto_completo(nome_produto="Produto B", codigo_barras="123")

    def test_reaproveita_categoria_existente_em_vez_de_duplicar(self):
        id1 = cadastrar_produto_completo(nome_produto="Produto A", nome_categoria="Bebidas")
        id2 = cadastrar_produto_completo(nome_produto="Produto B", nome_categoria="Bebidas")
        p1, p2 = buscar_por_id(id1), buscar_por_id(id2)
        assert p1.id_categoria == p2.id_categoria

    def test_cadastro_sem_dados_opcionais_funciona(self):
        id_produto = cadastrar_produto_completo(nome_produto="Produto Mínimo")
        produto = buscar_por_id(id_produto)
        assert produto.nome_produto == "Produto Mínimo"
        assert produto.codigo_barras is None


class TestBusca:
    def test_buscar_por_codigo_barras_encontra(self, produto_padrao):
        produto = buscar_por_codigo_barras("7891234567895")
        assert isinstance(produto, Produto)
        assert produto.id_produto == produto_padrao

    def test_buscar_por_codigo_barras_inexistente_devolve_none(self):
        assert buscar_por_codigo_barras("0000000000000") is None

    def test_buscar_por_id_inexistente_devolve_none(self):
        assert buscar_por_id(9999) is None

    def test_buscar_por_nome_encontra_por_substring(self, produto_padrao):
        resultados = buscar_por_nome("Tinto")
        assert len(resultados) == 1
        assert all(isinstance(p, Produto) for p in resultados)

    def test_listar_todos_devolve_lista_de_produto(self, produto_padrao):
        todos = listar_todos()
        assert all(isinstance(p, Produto) for p in todos)
        assert len(todos) == 1


class TestEdicao:
    def test_editar_nome(self, produto_padrao):
        editar_nome_produto(produto_padrao, "Novo Nome")
        assert buscar_por_id(produto_padrao).nome_produto == "Novo Nome"

    def test_editar_nome_vazio_mantem_o_atual(self, produto_padrao):
        editar_nome_produto(produto_padrao, "   ")
        assert buscar_por_id(produto_padrao).nome_produto == "Vinho Tinto Reserva"

    def test_editar_valor_unitario_rejeita_negativo(self, produto_padrao):
        with pytest.raises(ValueError, match="não pode ser negativo"):
            editar_valor_unitario(produto_padrao, -10)

    def test_editar_produto_inexistente_leva_erro(self):
        with pytest.raises(ValueError, match="não encontrado"):
            editar_nome_produto(9999, "Qualquer Nome")

    def test_editar_codigo_barras_para_um_ja_usado_por_outro_produto(self, produto_padrao):
        cadastrar_produto_completo(nome_produto="Outro Produto", codigo_barras="999")
        with pytest.raises(ValueError):
            editar_codigo_barras(produto_padrao, "999")


class TestExclusao:
    def test_excluir_marca_produto_como_inativo(self, produto_padrao):
        assert excluir_produto(produto_padrao) is True
        # buscar_por_id só enxerga produtos ativos (produto desativado =
        # produto excluído, por design) -- por isso passa a devolver None
        assert buscar_por_id(produto_padrao) is None

    def test_excluir_produto_ja_excluido_nao_reexecuta(self, produto_padrao):
        excluir_produto(produto_padrao)
        assert excluir_produto(produto_padrao) is False  # já estava inativo

    def test_reativar_produto(self, produto_padrao):
        excluir_produto(produto_padrao)
        assert reativar_produto(produto_padrao) is True
        assert buscar_por_id(produto_padrao).ativo is True

    def test_produto_desativado_nao_pode_ter_estoque_editado(self, produto_padrao):
        excluir_produto(produto_padrao)
        with pytest.raises(ValueError, match="desativado"):
            atualizar_campo_estoque(
                produto_padrao, "estoque_deposito", 100,
                contexto="editar", exigir_existente=True,
            )
