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