from caixa.Caixa import caixa

def menu():
    print("=====  menu ======")
    print("1 - Acessar Caixa")
    print("2 - Acessar Estoque")
    print("3 - Acessar Geladeira")

    print()
    opcao = input("Insira uma opção: ")
    match opcao:
        case "1":
            caixa()
        case "2":
            print("Acessar Estoque")
        case "3":
            print("Acessar Geladeira")
        case "4":
            print("Menu extra")
        case "5":
            print("Menu extra 2")
        case "6":
            print("Menu extra 3")