from controllers.produto_controller import executar_cadastro, executar_busca, executar_edicao,executar_exclusao, executar_reativacao

def menu_produtos():
    while True:
        print("\n====== PRODUTOS ======")
        print("1 - Cadastrar produto")
        print("2 - Buscar produto")
        print("3 - Editar produto")
        print("4 - Excluir/Desativar produto")
        print("5 - Reativar produto")
        print("0 - Voltar")
        opcao = input("\nEscolha: ")

        if opcao == "1":
            executar_cadastro()
        elif opcao == "2":
            executar_busca()
        elif opcao == "3":
            executar_edicao()
        elif opcao == "4":
            executar_exclusao()
        elif opcao == "5":
            executar_reativacao()
        elif opcao == "0":
           break
        else:
            print("Opção inválida.")