from utils.leitor_barras import codigo_lido
from services.buscar_produto import *

print("Teste de busca, passe o codigo")
codigo = codigo_lido()


print("Aqui é suposto ver o que achou: ")
produto = buscar_por_codigo_barras(codigo)
print(produto)

print("Teste com nome agora")
nome = input("Digite o nome do produto: ")

print("Aqui é suposto ver o que achou: ")
produto = buscar_por_nome(nome)
print(produto)

print("aqui vai listar tudo")
produtos = listar_todos()
for produto in produtos:
    print(produto)