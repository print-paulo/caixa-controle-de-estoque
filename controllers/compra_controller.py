#tem que importar as funções que serão criadas

def menu_compras():

    while True:

        print("""
======= COMPRAS =======

1 - Registrar compra
2 - Buscar compra
0 - Voltar

=======================
""")

        opcao = input("Escolha: ")

        match opcao:

            case "1":
                #registrar_compra()
                pass
            case "2":
                #buscar_compra()
                pass
            case "0":
                break