import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controllers.estoque_controller import (
    executar_consulta,
    executar_produtos_abaixo_minimo,
    executar_reposicao,
    executar_ajuste,
    executar_historico,
)

def menu_estoque():

    while True:

        print("\n====== ESTOQUE ======")
        print("1 - Consultar estoque")
        print("2 - Produtos abaixo do mínimo")
        print("3 - Repor exposição")
        print("4 - Ajustar estoque")
        print("5 - Histórico")
        print("0 - Voltar")

        opcao = input("\nEscolha: ")

        if opcao == "1":
            executar_consulta()

        elif opcao == "2":
            executar_produtos_abaixo_minimo()

        elif opcao == "3":
            executar_reposicao()

        elif opcao == "4":
            executar_ajuste()

        elif opcao == "5":
            executar_historico()

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")