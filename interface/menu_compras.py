import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controllers.compra_controller import executar_compra, executar_busca_compra


def menu_compras():

    while True:

        print("\n====== COMPRAS ======")
        print("1 - Registrar compra")
        print("2 - Buscar compra")
        print("3 - Cancelar compra")
        print("0 - Voltar")

        opcao = input("\nEscolha: ")

        if opcao == "1":
            executar_compra()

        elif opcao == "2":
            executar_busca_compra()

        elif opcao == "3":
            # Mesmo caso do menu de vendas: ainda não existe um controller
            # pra cancelar uma compra aberta específica fora do fluxo -- hoje
            # o cancelamento só acontece dentro do próprio executar_compra.
            print("Ainda não implementado.")

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")