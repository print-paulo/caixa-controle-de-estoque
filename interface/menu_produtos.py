from tests.cadastro_teste import executar_cadastro
#from tests.buscar_teste import executar_busca
#from tests.editar_teste import executar_edicao
#from tests.excluir_teste import executar_exclusao

#   depois é pra criar as funções de teste e dps mudar elas de pasta pra uma função real
def menu_produtos():

    while True:

        print("\n====== PRODUTOS ======")
        print("1 - Cadastrar produto")
        print("2 - Buscar produto")
        print("3 - Editar produto")
        print("4 - Excluir produto")
        print("0 - Voltar")

        opcao = input("\nEscolha: ")

        if opcao == "1":
            executar_cadastro()

        elif opcao == "2":
            #executar_busca()
            pass

        elif opcao == "3":
            #executar_edicao()
            pass
        elif opcao == "4":
            #executar_exclusao()
            pass
        elif opcao == "0":
            break

        else:
            print("Opção inválida.")