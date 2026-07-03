
def caixa():
    print("Caixa exemplo")

    opcao =  input("bem vindo ao caixa, selecione sua opcao")

    match opcao:
        case "1":
            print("Começar a Vender")
        case "2":
            print("Verificar Vendas")
        case "3":
            print("Sair")
