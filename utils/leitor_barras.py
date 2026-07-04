def codigo_lido():
    codigo = input()

    while True:
        if len(codigo) == 13:
            return codigo
        elif codigo == "sair":
            break
        else:
            print("Código invalido")