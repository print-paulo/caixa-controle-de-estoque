#from tests.registrar_venda_teste import executar_venda
#from tests.buscar_venda_teste import executar_busca_venda

#novamente criar as funções dps e mudar seus locais pra funções reais

def menu_vendas():

    while True:

        print("\n====== VENDAS ======")
        print("1 - Nova venda")
        print("2 - Buscar venda")
        print("3 - Cancelar venda")
        print("0 - Voltar")

        opcao = input()

        if opcao == "1":
            #executar_venda()
            pass

        elif opcao == "2":
            #executar_busca_venda()
            pass
        elif opcao == "3":
            pass

        elif opcao == "0":
            break