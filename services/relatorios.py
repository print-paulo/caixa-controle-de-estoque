import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.conectar_banco import conectar_banco


def _filtro_periodo(campo_data, data_inicio, data_fim):
    """
    Monta a cláusula WHERE (e os parâmetros) pra filtrar por período,
    usando date(campo_data) para comparar só a data, ignorando a hora.
    `data_inicio`/`data_fim` no formato 'YYYY-MM-DD'. Qualquer um dos
    dois pode ser None (sem limite naquele lado).
    """
    condicoes = []
    parametros = []

    if data_inicio:
        condicoes.append(f"date({campo_data}) >= date(?)")
        parametros.append(data_inicio)

    if data_fim:
        condicoes.append(f"date({campo_data}) <= date(?)")
        parametros.append(data_fim)

    return condicoes, parametros


# ---------- relatório de produtos ----------

def relatorio_produtos():
    """
    Retorna um dicionário com:
    - total_ativos: quantidade de produtos ativos
    - total_inativos: quantidade de produtos desativados
    - por_categoria: lista de (nome_categoria, quantidade_produtos)
    - sem_preco: lista de produtos ativos sem valor_unitario definido
    """
    conn = conectar_banco()
    try:
        total_ativos = conn.execute(
            "SELECT COUNT(*) FROM produto WHERE ativo = 1"
        ).fetchone()[0]

        total_inativos = conn.execute(
            "SELECT COUNT(*) FROM produto WHERE ativo = 0"
        ).fetchone()[0]

        por_categoria = conn.execute("""
            SELECT COALESCE(c.nome_categoria, 'SEM CATEGORIA'), COUNT(*)
            FROM produto p
            LEFT JOIN categoria c ON c.id_categoria = p.id_categoria
            WHERE p.ativo = 1
            GROUP BY c.nome_categoria
            ORDER BY COUNT(*) DESC
        """).fetchall()

        sem_preco = conn.execute("""
            SELECT id_produto, nome_produto
            FROM produto
            WHERE ativo = 1 AND (valor_unitario IS NULL)
            ORDER BY nome_produto
        """).fetchall()

        return {
            "total_ativos": total_ativos,
            "total_inativos": total_inativos,
            "por_categoria": por_categoria,
            "sem_preco": sem_preco,
        }
    finally:
        conn.close()


# ---------- relatório de estoque ----------

def relatorio_estoque():
    """
    Retorna um dicionário com:
    - valor_total_estoque: soma de valor_unitario * (deposito + exposicao)
      dos produtos ativos com preço definido
    - quantidade_total_unidades: soma de todas as unidades (deposito + exposicao)
    - produtos_abaixo_minimo: quantidade de produtos no mínimo ou abaixo
    """
    conn = conectar_banco()
    try:
        valor_total = conn.execute("""
            SELECT COALESCE(SUM((e.estoque_deposito + e.estoque_exposicao) * p.valor_unitario), 0)
            FROM estoque e
            JOIN produto p ON p.id_produto = e.id_produto
            WHERE p.ativo = 1 AND p.valor_unitario IS NOT NULL
        """).fetchone()[0]

        quantidade_total = conn.execute("""
            SELECT COALESCE(SUM(e.estoque_deposito + e.estoque_exposicao), 0)
            FROM estoque e
            JOIN produto p ON p.id_produto = e.id_produto
            WHERE p.ativo = 1
        """).fetchone()[0]

        abaixo_minimo = conn.execute("""
            SELECT COUNT(*)
            FROM estoque e
            JOIN produto p ON p.id_produto = e.id_produto
            WHERE p.ativo = 1
              AND e.estoque_minimo IS NOT NULL
              AND e.estoque_deposito <= e.estoque_minimo
        """).fetchone()[0]

        return {
            "valor_total_estoque": valor_total,
            "quantidade_total_unidades": quantidade_total,
            "produtos_abaixo_minimo": abaixo_minimo,
        }
    finally:
        conn.close()


# ---------- relatório de vendas ----------

def relatorio_vendas(data_inicio=None, data_fim=None):
    """
    Relatório de vendas FINALIZADAS num período (ambas as datas opcionais,
    formato 'YYYY-MM-DD'; sem elas, considera todo o histórico).

    Retorna um dicionário com:
    - quantidade_vendas: nº de vendas finalizadas no período
    - total_vendido: soma dos totais das vendas
    - ticket_medio: total_vendido / quantidade_vendas (0 se não houver vendas)
    - por_forma_pagamento: lista de (forma_pagamento, quantidade, total)
    """
    conn = conectar_banco()
    try:
        condicoes, parametros = _filtro_periodo("v.data_hora", data_inicio, data_fim)
        condicoes.insert(0, "v.status = 'FINALIZADA'")
        where = f"WHERE {' AND '.join(condicoes)}"

        resumo = conn.execute(f"""
            SELECT COUNT(*), COALESCE(SUM(v.valor_total), 0)
            FROM venda v
            {where}
        """, parametros).fetchone()

        quantidade_vendas, total_vendido = resumo
        ticket_medio = (total_vendido / quantidade_vendas) if quantidade_vendas else 0.0

        por_forma_pagamento = conn.execute(f"""
            SELECT v.forma_pagamento, COUNT(*), COALESCE(SUM(v.valor_total), 0)
            FROM venda v
            {where}
            GROUP BY v.forma_pagamento
            ORDER BY SUM(v.valor_total) DESC
        """, parametros).fetchall()

        return {
            "quantidade_vendas": quantidade_vendas,
            "total_vendido": total_vendido,
            "ticket_medio": ticket_medio,
            "por_forma_pagamento": por_forma_pagamento,
        }
    finally:
        conn.close()


# ---------- relatório de compras ----------

def relatorio_compras(data_inicio=None, data_fim=None):
    """
    Relatório de compras FINALIZADAS num período (mesmas regras de data
    do relatório de vendas).

    Retorna um dicionário com:
    - quantidade_compras: nº de compras finalizadas no período
    - total_investido: soma dos totais (em custo) das compras
    - lucro_esperado_total: soma de (valor_venda_calculado - valor_custo_unitario)
      * quantidade de cada item comprado no período -- é o lucro que se
      espera obter SE tudo que foi comprado for vendido pelo preço
      calculado. Diferente do lucro_real do relatório de lucro (que só
      conta o que já foi vendido de verdade), esse é um lucro projetado
      no momento da compra.
    - por_fornecedor: lista de (fornecedor, quantidade, total)
    """
    conn = conectar_banco()
    try:
        condicoes, parametros = _filtro_periodo("c.data_hora", data_inicio, data_fim)
        condicoes.insert(0, "c.status = 'FINALIZADA'")
        where = f"WHERE {' AND '.join(condicoes)}"

        resumo = conn.execute(f"""
            SELECT
                COUNT(DISTINCT c.id_compra),
                COALESCE(SUM(ic.sub_total), 0),
                COALESCE(SUM((ic.valor_venda_calculado - ic.valor_custo_unitario) * ic.quantidade), 0)
            FROM compra c
            JOIN item_compra ic ON ic.id_compra = c.id_compra
            {where}
        """, parametros).fetchone()

        quantidade_compras, total_investido, lucro_esperado_total = resumo

        por_fornecedor = conn.execute(f"""
            SELECT COALESCE(c.fornecedor, 'NÃO INFORMADO'), COUNT(DISTINCT c.id_compra), COALESCE(SUM(ic.sub_total), 0)
            FROM compra c
            JOIN item_compra ic ON ic.id_compra = c.id_compra
            {where}
            GROUP BY c.fornecedor
            ORDER BY SUM(ic.sub_total) DESC
        """, parametros).fetchall()

        return {
            "quantidade_compras": quantidade_compras,
            "total_investido": total_investido,
            "lucro_esperado_total": lucro_esperado_total,
            "por_fornecedor": por_fornecedor,
        }
    finally:
        conn.close()


# ---------- relatório de lucro ----------

def relatorio_lucro(data_inicio=None, data_fim=None):
    """
    Retorna dois números de lucro diferentes, lado a lado:

    - lucro_bruto: total vendido - total investido em compras no período
      (regime de caixa -- compara o que entrou de vendas com o que saiu
      em compras no mesmo período). É uma APROXIMAÇÃO: se você compra um
      lote grande e vende só uma parte no período, esse número fica
      distorcido (parece prejuízo mesmo quando cada unidade vendida deu
      lucro de verdade), porque mistura "dinheiro investido em estoque"
      com "lucro de vendas realizadas".

    - lucro_real: soma de (preço de venda - custo) * quantidade, calculado
      por cada item efetivamente VENDIDO no período, usando o custo que
      estava congelado no produto no momento daquela venda
      (`item_venda.custo_unitario_momento`). Isso é a margem de verdade
      das vendas que já aconteceram, sem ser afetado pelo que ainda está
      parado no estoque.

    Se algum item foi vendido sem custo registrado (produto que nunca
    passou por uma compra no sistema, ou vendido antes dessa métrica
    existir), ele fica de fora do lucro_real -- a quantidade de unidades
    nessa situação vem em `unidades_sem_custo_registrado`, pra deixar
    claro quando o número pode estar incompleto.

    Retorna um dicionário com: total_vendido, total_investido, lucro_bruto,
    lucro_real, unidades_sem_custo_registrado.
    """
    vendas = relatorio_vendas(data_inicio, data_fim)
    compras = relatorio_compras(data_inicio, data_fim)

    total_vendido = vendas["total_vendido"]
    total_investido = compras["total_investido"]

    lucro_real, unidades_sem_custo = _calcular_lucro_real(data_inicio, data_fim)

    return {
        "total_vendido": total_vendido,
        "total_investido": total_investido,
        "lucro_bruto": total_vendido - total_investido,
        "lucro_real": lucro_real,
        "unidades_sem_custo_registrado": unidades_sem_custo,
    }


def _calcular_lucro_real(data_inicio=None, data_fim=None):
    """
    Soma (valor_unitario_momento - custo_unitario_momento) * quantidade
    de cada item de venda finalizada no período. Itens sem custo
    registrado (custo_unitario_momento NULL) são ignorados na soma, mas
    contados à parte.
    """
    conn = conectar_banco()
    try:
        condicoes, parametros = _filtro_periodo("v.data_hora", data_inicio, data_fim)
        condicoes.insert(0, "v.status = 'FINALIZADA'")
        where = f"WHERE {' AND '.join(condicoes)}"

        resultado = conn.execute(f"""
            SELECT
                COALESCE(SUM(
                    CASE WHEN iv.custo_unitario_momento IS NOT NULL
                         THEN (iv.valor_unitario_momento - iv.custo_unitario_momento) * iv.quantidade
                         ELSE 0
                    END
                ), 0),
                COALESCE(SUM(
                    CASE WHEN iv.custo_unitario_momento IS NULL THEN iv.quantidade ELSE 0 END
                ), 0)
            FROM item_venda iv
            JOIN venda v ON v.id_venda = iv.id_venda
            {where}
        """, parametros).fetchone()

        lucro_real, unidades_sem_custo = resultado
        return lucro_real, unidades_sem_custo
    finally:
        conn.close()