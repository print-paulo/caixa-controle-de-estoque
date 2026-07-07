def validar_nao_negativo(valor, nome_campo, feminino=False, permitir_none=True):
    """
    Valida que `valor` não é negativo, levantando ValueError caso seja.
 
    - feminino: usa "negativa" em vez de "negativo" na mensagem
      (ex: "Quantidade não pode ser negativa.").
    - permitir_none: se False, trata None como inválido também
      (mesma mensagem de "não pode ser negativo").
    """
    sufixo = "negativa" if feminino else "negativo"
 
    if valor is None:
        if permitir_none:
            return
        raise ValueError(f"{nome_campo} não pode ser {sufixo}.")
 
    if valor < 0:
        raise ValueError(f"{nome_campo} não pode ser {sufixo}.")


def validar_positivo(valor, nome_campo):
    """
    Valida que `valor` é maior que zero, levantando ValueError caso não seja
    (usada em casos onde zero ou None não fazem sentido, como quantidade vendida).
    """
    if valor is None or valor <= 0:
        raise ValueError(f"{nome_campo} deve ser maior que zero.")