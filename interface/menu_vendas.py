import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controllers.venda_controller import executar_venda, executar_busca_venda


def menu_vendas():

    while True:

        print("\n====== VENDAS ======")
        print("1 - Nova venda")
        print("2 - Buscar venda")
        print("3 - Cancelar venda")
        print("0 - Voltar")

        opcao = input("\nEscolha: ")

        if opcao == "1":
            executar_venda()

        elif opcao == "2":
            executar_busca_venda()

        elif opcao == "3":
            # Ainda não existe um controller pra cancelar uma venda aberta
            # específica fora do fluxo -- hoje o cancelamento só acontece
            # dentro do próprio executar_venda (quando não tem item ou o
            # usuário não confirma no final).
            print("Ainda não implementado.")

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")