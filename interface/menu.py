import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from interface.menu_produtos import menu_produtos
from interface.menu_vendas import menu_vendas
from interface.menu_compras import menu_compras
from interface.menu_estoque import menu_estoque
from interface.menu_relatorios import menu_relatorios


def menu():

    while True:

        print("\n========== MERCADO ==========")
        print("1 - Produtos")
        print("2 - Vendas")
        print("3 - Compras")
        print("4 - Estoque")
        print("5 - Relatórios")
        print("0 - Sair")

        opcao = input("\nEscolha: ")

        if opcao == "1":
            menu_produtos()

        elif opcao == "2":
            menu_vendas()

        elif opcao == "3":
            menu_compras()

        elif opcao == "4":
            menu_estoque()

        elif opcao == "5":
            menu_relatorios()

        elif opcao == "0":
            print("Encerrando...")
            break

        else:
            print("Opção inválida.")