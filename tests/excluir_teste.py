import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from controllers.produto_controller import executar_exclusao, executar_reativacao

if __name__ == "__main__":
    while True:
        escolha = input("1 pra excluir, 2 pra reativar \n")
        if escolha == "1":
            executar_exclusao()
        elif escolha == "2":
            executar_reativacao()
        elif escolha == "sair":
            break
        else:
            pass
