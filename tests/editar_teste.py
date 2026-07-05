import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import services.editar_produto as edit
from services.buscar_produto import buscar_nome_por_id

if __name__ == "__main__":
    # Teste rápido manual
    id_produto = int(input("Id do produto a editar: "))
    produto = buscar_nome_por_id(id_produto)
    
    print(f"Produto atual: {produto}")
    
    edit.editar_nome_produto(id_produto, input("Novo nome do produto: ").upper())
    
    edit.editar_categoria(id_produto, input("Nova categoria: ").upper())
    
    edit.editar_codigo_barras(id_produto, input("Novo código de barras: "))
    
    nova_quantidade = input("Nova quantidade: ")
    nova_quantidade = None if nova_quantidade == "" else int(nova_quantidade) # Permite deixar em branco para não alterar
    edit.editar_quantidade(id_produto, nova_quantidade) 
    
    edit.editar_medida_quantidade(id_produto, input("Nova medida de quantidade: "))
    
    novo_valor_unitario = input("Novo valor unitário: ")
    novo_valor_unitario = None if novo_valor_unitario == "" else float(novo_valor_unitario) # Permite deixar em branco para não alterar
    edit.editar_valor_unitario(id_produto, novo_valor_unitario)

    print("Valor unitário atualizado.")