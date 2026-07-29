import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.relatorios import (
    relatorio_produtos,
    relatorio_estoque,
    relatorio_vendas,
    relatorio_compras,
    relatorio_lucro,
)


def _pedir_periodo():
    """Pergunta data inicial/final (opcionais). Enter em qualquer uma pula o limite."""
    print("(Formato AAAA-MM-DD. Deixe em branco pra não limitar)")
    data_inicio = input("Data inicial: ").strip() or None
    data_fim = input("Data final: ").strip() or None
    return data_inicio, data_fim


# ----------- produtos --------------

def executar_relatorio_produtos():
    relatorio = relatorio_produtos()

    print(f"\nProdutos ativos: {relatorio['total_ativos']}")
    print(f"Produtos desativados: {relatorio['total_inativos']}")

    print("\nPor categoria:")
    for nome_categoria, quantidade in relatorio["por_categoria"]:
        print(f"  {nome_categoria}: {quantidade}")

    if relatorio["sem_preco"]:
        print("\nProdutos ativos sem preço cadastrado:")
        for id_produto, nome in relatorio["sem_preco"]:
            print(f"  [{id_produto}] {nome}")


# ----------- estoque --------------

def executar_relatorio_estoque():
    relatorio = relatorio_estoque()

    print(f"\nValor total em estoque: R$ {relatorio['valor_total_estoque']:.2f}")
    print(f"Quantidade total de unidades: {relatorio['quantidade_total_unidades']}")
    print(f"Produtos no mínimo ou abaixo dele: {relatorio['produtos_abaixo_minimo']}")


# ----------- vendas --------------

def executar_relatorio_vendas():
    data_inicio, data_fim = _pedir_periodo()
    relatorio = relatorio_vendas(data_inicio, data_fim)

    print(f"\nVendas finalizadas: {relatorio['quantidade_vendas']}")
    print(f"Total vendido: R$ {relatorio['total_vendido']:.2f}")
    print(f"Ticket médio: R$ {relatorio['ticket_medio']:.2f}")

    if relatorio["por_forma_pagamento"]:
        print("\nPor forma de pagamento:")
        for forma, quantidade, total in relatorio["por_forma_pagamento"]:
            print(f"  {forma or 'NÃO INFORMADA'}: {quantidade} venda(s) — R$ {total:.2f}")


# ----------- compras --------------

def executar_relatorio_compras():
    data_inicio, data_fim = _pedir_periodo()
    relatorio = relatorio_compras(data_inicio, data_fim)

    print(f"\nCompras finalizadas: {relatorio['quantidade_compras']}")
    print(f"Total investido: R$ {relatorio['total_investido']:.2f}")
    print(f"Lucro esperado total (se tudo for vendido pelo preço calculado): R$ {relatorio['lucro_esperado_total']:.2f}")

    if relatorio["por_fornecedor"]:
        print("\nPor fornecedor:")
        for fornecedor, quantidade, total in relatorio["por_fornecedor"]:
            print(f"  {fornecedor}: {quantidade} compra(s) — R$ {total:.2f}")


# ----------- lucro --------------

def executar_relatorio_lucro():
    """
    Mostra dois números de lucro lado a lado:

    - Lucro bruto (regime de caixa): total vendido menos total investido
      em compras no período. Aproximação simples, mas distorce quando
      você compra mais do que vende no mesmo período.
    - Lucro real: soma da margem (preço de venda - custo) de cada
      unidade efetivamente vendida no período, usando o custo travado no
      momento de cada venda. Mais preciso, mas só existe pra vendas
      feitas depois que essa métrica passou a ser registrada -- vendas
      antigas ou de produtos sem custo cadastrado ficam de fora (ver
      aviso de unidades sem custo registrado).
    """
    data_inicio, data_fim = _pedir_periodo()
    relatorio = relatorio_lucro(data_inicio, data_fim)

    print(f"\nTotal vendido: R$ {relatorio['total_vendido']:.2f}")
    print(f"Total investido em compras: R$ {relatorio['total_investido']:.2f}")
    print(f"Lucro bruto (regime de caixa): R$ {relatorio['lucro_bruto']:.2f}")
    print(
        "  (aproximação: compara vendas e compras do período, "
        "não o custo exato de cada unidade vendida)"
    )
    print(f"\nLucro real (margem das vendas do período): R$ {relatorio['lucro_real']:.2f}")

    if relatorio["unidades_sem_custo_registrado"]:
        print(
            f"  Atenção: {relatorio['unidades_sem_custo_registrado']} unidade(s) vendida(s) "
            "sem custo registrado ficaram de fora desse cálculo."
        )