#tem que importar as funções que serão criadas

def menu_produtos():

    while True:

        print("""
====== PRODUTOS ======

1 - Cadastrar
2 - Buscar
3 - Editar
4 - Excluir
0 - Voltar

======================
""")

        opcao = input("Escolha: ")

        match opcao:

            case "1":
                #cadastrar_produto()
                pass
            case "2":
                #buscar_produto()
                pass
            case "3":
                #editar_produto()
                pass
            case "4":
                #excluir_produto()
                pass
            case "0":
                break

            case _:
                print("Opção inválida.")