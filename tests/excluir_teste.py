from services.excluir_produto import *

if __name__ == "__main__":

    print("Teste pra desativar/excluir um produto: ")

    id_produto = int(input("Informe o ID do produto: "))

    if excluir_produto(id_produto):
        print("Produto desativado com sucesso.")
    else:
        print("Produto não encontrado ou já estava desativado.")


    print("Agora teste pra reativar: ")
    id_produto = int(input("Informe o ID do produto: "))

    if reativar_produto(id_produto):
        print("Produto reativado com sucesso.")
    else:
        print("Produto não encontrado, ou ja está ativo")