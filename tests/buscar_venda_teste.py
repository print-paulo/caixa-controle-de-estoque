import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.buscar_venda import (
    buscar_venda_por_id,
    listar_itens_venda,
    listar_vendas,
    listar_vendas_por_produto,
)

if __name__ == "__main__":

    print("Teste de busca de venda, informe o id")
    id_venda = int(input("Id da venda: "))

    print("\nAqui é suposto ver os dados da venda: ")
    venda = buscar_venda_por_id(id_venda)
    print(venda)

    print("\nAqui vai listar os itens dessa venda: ")
    itens = listar_itens_venda(id_venda)
    for item in itens:
        print(item)

    print("\nAqui vai listar todas as vendas (mais recente primeiro): ")
    vendas = listar_vendas()
    for venda in vendas:
        print(venda)

    print("\nTeste com filtro de status agora")
    status = input("Digite o status pra filtrar (aberta/finalizada/cancelada, ou deixe em branco pra pular): ").strip()

    if status:
        print(f"\nAqui é suposto ver só as vendas com status '{status}': ")
        vendas_filtradas = listar_vendas(status=status)
        for venda in vendas_filtradas:
            print(venda)

    print("\nTeste com histórico de vendas por produto agora")
    id_produto = input("Digite o id do produto (ou deixe em branco pra pular): ").strip()

    if id_produto:
        print(f"\nAqui vai listar o histórico de vendas do produto {id_produto}: ")
        historico = listar_vendas_por_produto(int(id_produto))
        for registro in historico:
            print(registro)