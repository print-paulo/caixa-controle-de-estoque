from database.banco import criar_tabelas
from interface.menu import menu
from utils.conectar_banco import conectar_banco

if __name__ == '__main__':
    criar_tabelas(conn=conectar_banco())
    menu()