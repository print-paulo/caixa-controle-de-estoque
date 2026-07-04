def codigo_lido():
    while True:
        codigo = input().strip()

        if codigo.lower() == "sair": #Temporario pq precisa dps fazer que aperte o botão e saia
            return None

        if len(codigo) == 13 and codigo.isdigit():
            return codigo
        print("Código inválido.")