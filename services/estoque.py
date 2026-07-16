import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco
from utils.validacoes import validar_nao_negativo


def _produto_ativo_existe(conn, id_produto):
    existe = conn.execute(
        "SELECT 1 FROM produto WHERE id_produto = ? AND ativo = 1", (id_produto,)
    ).fetchone()
    if existe is None:
        raise ValueError(f"Produto com id {id_produto} não encontrado ou inativo.")


# ---------- consulta ----------

def consultar_estoque_por_id(id_produto):
    """
    Retorna os dados de estoque de um produto, já com o nome do produto
    (via JOIN): (id_produto, nome_produto, estoque_deposito,
    estoque_exposicao, capacidade_exposicao, estoque_minimo, ultima_atualizacao).
    """
    conn = conectar_banco()
    try:
        return conn.execute("""
            SELECT p.id_produto, p.nome_produto, e.estoque_deposito, e.estoque_exposicao,
                   e.capacidade_exposicao, e.estoque_minimo, e.ultima_atualizacao
            FROM estoque e
            JOIN produto p ON p.id_produto = e.id_produto
            WHERE e.id_produto = ?
        """, (id_produto,)).fetchone()
    finally:
        conn.close()


def listar_estoque_completo():
    """Lista o estoque de todos os produtos ativos, ordenado por nome."""
    conn = conectar_banco()
    try:
        return conn.execute("""
            SELECT p.id_produto, p.nome_produto, e.estoque_deposito, e.estoque_exposicao,
                   e.capacidade_exposicao, e.estoque_minimo, e.ultima_atualizacao
            FROM estoque e
            JOIN produto p ON p.id_produto = e.id_produto
            WHERE p.ativo = 1
            ORDER BY p.nome_produto
        """).fetchall()
    finally:
        conn.close()


def listar_produtos_abaixo_minimo():
    """
    Lista produtos cujo estoque de depósito está no mínimo ou abaixo dele
    (mesmo critério usado como alerta durante a venda). Serve como sinal
    de "hora de comprar mais", não significa que o produto já acabou --
    ainda pode haver unidades na exposição.
    """
    conn = conectar_banco()
    try:
        return conn.execute("""
            SELECT p.id_produto, p.nome_produto, e.estoque_deposito, e.estoque_exposicao, e.estoque_minimo
            FROM estoque e
            JOIN produto p ON p.id_produto = e.id_produto
            WHERE p.ativo = 1
              AND e.estoque_minimo IS NOT NULL
              AND e.estoque_deposito <= e.estoque_minimo
            ORDER BY p.nome_produto
        """).fetchall()
    finally:
        conn.close()


# ---------- reposição (depósito -> exposição) ----------

def repor_exposicao(id_produto, quantidade=None):
    """
    Move unidades do depósito para a exposição.

    - Se `quantidade` for None, repõe automaticamente até a capacidade de
      exposição (o máximo possível, limitado pelo que existe no depósito).
    - Se `quantidade` for informada, move exatamente esse valor -- e
      valida que não ultrapassa nem o depósito disponível, nem o espaço
      livre na exposição (quando há capacidade definida).

    Retorna a quantidade efetivamente movida.
    """
    conn = conectar_banco()
    try:
        _produto_ativo_existe(conn, id_produto)

        estoque = conn.execute("""
            SELECT estoque_deposito, estoque_exposicao, capacidade_exposicao
            FROM estoque WHERE id_produto = ?
        """, (id_produto,)).fetchone()

        if estoque is None:
            raise ValueError("Estoque do produto não encontrado.")

        deposito, exposicao, capacidade = estoque

        if quantidade is None:
            if capacidade is None or capacidade <= 0:
                raise ValueError("Produto não tem capacidade de exposição definida; informe a quantidade manualmente.")
            espaco_livre = max(capacidade - exposicao, 0)
            quantidade = min(espaco_livre, deposito)
            if quantidade == 0:
                return 0
        else:
            validar_nao_negativo(quantidade, "Quantidade", permitir_none=False)
            if quantidade > deposito:
                raise ValueError(f"Depósito não tem {quantidade} unidades disponíveis (atual: {deposito}).")
            if capacidade is not None and capacidade > 0 and (exposicao + quantidade) > capacidade:
                raise ValueError(
                    f"Isso ultrapassaria a capacidade de exposição ({capacidade}). "
                    f"Espaço livre atual: {max(capacidade - exposicao, 0)}."
                )

        conn.execute("""
            UPDATE estoque
            SET estoque_deposito = estoque_deposito - ?,
                estoque_exposicao = estoque_exposicao + ?,
                ultima_atualizacao = CURRENT_TIMESTAMP
            WHERE id_produto = ?
        """, (quantidade, quantidade, id_produto))

        conn.commit()
        return quantidade

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------- ajuste manual ----------

def _ajustar_campo_estoque(id_produto, coluna, delta):
    """
    Função interna: soma `delta` (pode ser negativo) ao valor atual de
    uma coluna numérica da tabela estoque, sem deixar o resultado ficar
    negativo. Usada para correções manuais (perda, quebra, contagem
    física divergente etc.), diferente de `editar_estoque_*` que
    sobrescreve o valor absoluto durante a edição do cadastro.
    """
    conn = conectar_banco()
    try:
        _produto_ativo_existe(conn, id_produto)

        atual = conn.execute(
            f"SELECT {coluna} FROM estoque WHERE id_produto = ?", (id_produto,)
        ).fetchone()

        if atual is None:
            raise ValueError("Estoque do produto não encontrado.")

        novo_valor = atual[0] + delta
        if novo_valor < 0:
            raise ValueError(f"Ajuste inválido: resultaria em {coluna} negativo (atual: {atual[0]}, delta: {delta}).")

        conn.execute(f"""
            UPDATE estoque
            SET {coluna} = ?, ultima_atualizacao = CURRENT_TIMESTAMP
            WHERE id_produto = ?
        """, (novo_valor, id_produto))

        conn.commit()
        return novo_valor

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ajustar_estoque_deposito(id_produto, delta):
    """Soma `delta` (positivo ou negativo) ao estoque de depósito. Retorna o novo valor."""
    return _ajustar_campo_estoque(id_produto, "estoque_deposito", delta)


def ajustar_estoque_exposicao(id_produto, delta):
    """Soma `delta` (positivo ou negativo) ao estoque de exposição. Retorna o novo valor."""
    return _ajustar_campo_estoque(id_produto, "estoque_exposicao", delta)