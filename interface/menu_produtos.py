from controllers.produto_controller import executar_cadastro, executar_busca

def menu_produtos():
    while True:
        print("\n====== PRODUTOS ======")
        print("1 - Cadastrar produto")
        print("2 - Buscar produto")
        print("0 - Voltar")
        opcao = input("\nEscolha: ")

        if opcao == "1":
            executar_cadastro()
        elif opcao == "2":
            executar_busca()
        elif opcao == "0":
            break
        else:
            print("Opção inválida.")