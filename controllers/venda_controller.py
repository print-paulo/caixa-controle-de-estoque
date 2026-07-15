#tem que importar as funções que serão criadas

def menu_vendas():

    while True:

        print("""
======== VENDAS ========

1 - Registrar venda
2 - Buscar venda
0 - Voltar

========================
""")

        opcao = input("Escolha: ")

        match opcao:

            case "1":
                #registrar_venda()
                pass
            case "2":
                #buscar_venda()
                pass
            case "0":
                break