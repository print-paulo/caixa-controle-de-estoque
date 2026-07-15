import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.editar_produto import editar_nome_produto, editar_categoria, editar_codigo_barras, editar_quantidade, editar_medida_quantidade, editar_unidade, editar_valor_unitario, editar_estoque_deposito, editar_estoque_exposicao
from services.buscar_produto import buscar_nome_por_id

if __name__ == "__main__":
    # Teste rápido manual
    id_produto = int(input("Id do produto a editar: "))
    produto = buscar_nome_por_id(id_produto)
    
    print(f"Produto atual: {produto}")
    
    editar_nome_produto(id_produto, input("Novo nome do produto: ").upper())
    
    editar_categoria(id_produto, input("Nova categoria: ").upper())
    
    editar_codigo_barras(id_produto, input("Novo código de barras: "))
    
    nova_quantidade = input("Nova quantidade: ")
    nova_quantidade = None if nova_quantidade == "" else int(nova_quantidade) # Permite deixar em branco para não alterar
    editar_quantidade(id_produto, nova_quantidade) 
    
    editar_medida_quantidade(id_produto, input("Nova quantidade: (ex: 750ml, 2l)").upper())
    
    editar_unidade(id_produto, input("Nova unidade: ").upper())
    
    novo_valor_unitario = input("Novo valor unitário: ")
    novo_valor_unitario = None if novo_valor_unitario == "" else float(novo_valor_unitario) # Permite deixar em branco para não alterar
    editar_valor_unitario(id_produto, novo_valor_unitario)

    print("Valor unitário atualizado.")

    novo_estoque_deposito = input("Novo estoque disponível (depósito): ")
    novo_estoque_deposito = None if novo_estoque_deposito == "" else int(novo_estoque_deposito) # Permite deixar em branco para não alterar
    editar_estoque_deposito(id_produto, novo_estoque_deposito)

    novo_estoque_exposicao = input("Novo estoque em exibição: ")
    novo_estoque_exposicao = None if novo_estoque_exposicao == "" else int(novo_estoque_exposicao) # Permite deixar em branco para não alterar
    editar_estoque_exposicao(id_produto, novo_estoque_exposicao)

    print("Estoque atualizado.")