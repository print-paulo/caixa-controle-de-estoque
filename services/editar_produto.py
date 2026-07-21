import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.buscar_produto import buscar_por_id, buscar_nome_por_id, buscar_codigo_barras_por_id, buscar_categoria_por_id, buscar_quantidade_por_id, buscar_unidade_por_id, buscar_valor_unitario_por_id
from utils.leitor_barras import codigo_lido
from utils.conectar_banco import conectar_banco
from utils.validacoes import validar_nao_negativo
from utils.db_campos import atualizar_campo_produto, atualizar_campo_estoque

PASTA_SCRIPT = Path(__file__).resolve().parent
BANCO = PASTA_SCRIPT.parent / "database" / "banco.db"


def _produto_existe(id_produto):
    if buscar_por_id(id_produto) is None:
        raise ValueError(f"Produto com id {id_produto} não encontrado.")


def _atualizar_campo_produto(id_produto, coluna, valor):
    """Função interna: faz o UPDATE de uma única coluna da tabela produto."""
    return atualizar_campo_produto(id_produto, coluna, valor, contexto="editar", validar_existe=_produto_existe)


def _atualizar_campo_estoque(id_produto, coluna, valor):
    """Função interna: faz o UPDATE de uma única coluna da tabela estoque."""
    return atualizar_campo_estoque(id_produto, coluna, valor, contexto="editar", exigir_existente=True)


# ---------- campos da tabela produto ----------

def editar_nome_produto(id_produto, novo_nome):
    if not novo_nome or not novo_nome.strip():
        return buscar_nome_por_id(id_produto)
    return _atualizar_campo_produto(id_produto, "nome_produto", novo_nome.strip())


def editar_categoria(id_produto, nova_categoria):
    """Recebe o NOME da categoria; busca ou cria a categoria e associa o id ao produto."""
    conn = conectar_banco()
    try:
        id_categoria = None
        if nova_categoria and nova_categoria.strip():
            nova_categoria = nova_categoria.strip()
            resultado = conn.execute(
                "SELECT id_categoria FROM categoria WHERE nome_categoria = ?", (nova_categoria,)
            ).fetchone()
            if resultado:
                id_categoria = resultado[0]
            else:
                cursor = conn.execute(
                    "INSERT INTO categoria (nome_categoria) VALUES (?)", (nova_categoria,)
                )
                id_categoria = cursor.lastrowid
        elif not nova_categoria and nova_categoria.strip() == "":
            return buscar_categoria_por_id(id_produto) # Se a categoria for uma string vazia, não faz nada e retorna a categoria atual.
        
        _produto_existe(id_produto)
        conn.execute("UPDATE produto SET id_categoria = ? WHERE id_produto = ?", (id_categoria, id_produto))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao editar categoria: {e}")
    finally:
        conn.close()


def editar_codigo_barras(id_produto, novo_codigo_barras):
    if not novo_codigo_barras or not novo_codigo_barras.strip():
        return buscar_codigo_barras_por_id(id_produto) # Se o código de barras for uma string vazia, não faz nada e retorna o código de barras atual.
    return _atualizar_campo_produto(id_produto, "codigo_barras", novo_codigo_barras)


def editar_codigo_barras_com_leitor(id_produto):
    """Lê o novo código de barras direto do leitor, em vez de receber por parâmetro."""
    print("Aponte o leitor para o novo código de barras (ou digite 'sair' para cancelar):")
    codigo = codigo_lido()
    if codigo is None:
        print("Edição cancelada.")
        return False
    return editar_codigo_barras(id_produto, codigo)


def editar_quantidade(id_produto, nova_quantidade):
    if not nova_quantidade or not nova_quantidade.strip():
        return buscar_quantidade_por_id(id_produto) # Se a quantidade for uma string vazia, não faz nada e retorna a quantidade atual.
    return _atualizar_campo_produto(id_produto, "quantidade", nova_quantidade)


def editar_unidade(id_produto, nova_unidade):
    if not nova_unidade or not nova_unidade.strip():
        return buscar_unidade_por_id(id_produto) # Se a unidade for uma string vazia, não faz nada e retorna a unidade atual.
    return _atualizar_campo_produto(id_produto, "unidade", nova_unidade)


def editar_valor_unitario(id_produto, novo_valor):
    if novo_valor is None:
        return buscar_valor_unitario_por_id(id_produto) # Se o valor unitário for None, não faz nada e retorna o valor atual.
    validar_nao_negativo(novo_valor, "Valor unitário")
    return _atualizar_campo_produto(id_produto, "valor_unitario", novo_valor)


# ---------- campos da tabela estoque ----------

def editar_estoque_deposito(id_produto, novo_valor):
    validar_nao_negativo(novo_valor, "Estoque de depósito")
    return _atualizar_campo_estoque(id_produto, "estoque_deposito", novo_valor)


def editar_estoque_exposicao(id_produto, novo_valor):
    validar_nao_negativo(novo_valor, "Estoque de exposição")
    return _atualizar_campo_estoque(id_produto, "estoque_exposicao", novo_valor)


def editar_capacidade_exposicao(id_produto, novo_valor):
    validar_nao_negativo(novo_valor, "Capacidade de exposição", feminino=True)
    return _atualizar_campo_estoque(id_produto, "capacidade_exposicao", novo_valor)


def editar_estoque_minimo(id_produto, novo_valor):
    validar_nao_negativo(novo_valor, "Estoque mínimo")
    return _atualizar_campo_estoque(id_produto, "estoque_minimo", novo_valor)