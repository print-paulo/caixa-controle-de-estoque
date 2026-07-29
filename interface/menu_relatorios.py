import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controllers.relatorios_controller import (
    executar_relatorio_produtos,
    executar_relatorio_estoque,
    executar_relatorio_vendas,
    executar_relatorio_compras,
    executar_relatorio_lucro,
    executar_exportar_excel,
)


def menu_relatorios():

    while True:

        print("\n====== RELATÓRIOS ======")
        print("1 - Produtos")
        print("2 - Estoque")
        print("3 - Vendas")
        print("4 - Compras")
        print("5 - Lucro")
        print("6 - Exportar tudo para Excel")
        print("0 - Voltar")

        opcao = input("\nEscolha: ")

        if opcao == "1":
            executar_relatorio_produtos()

        elif opcao == "2":
            executar_relatorio_estoque()

        elif opcao == "3":
            executar_relatorio_vendas()

        elif opcao == "4":
            executar_relatorio_compras()

        elif opcao == "5":
            executar_relatorio_lucro()

        elif opcao == "6":
            executar_exportar_excel()

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")