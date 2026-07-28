import pytest

from utils.validacoes import validar_nao_negativo, validar_positivo


class TestValidarNaoNegativo:
    def test_aceita_valor_positivo(self):
        validar_nao_negativo(10, "Quantidade")  # não levanta

    def test_aceita_zero(self):
        validar_nao_negativo(0, "Quantidade")  # não levanta

    def test_rejeita_negativo(self):
        with pytest.raises(ValueError, match="não pode ser negativo"):
            validar_nao_negativo(-1, "Quantidade")

    def test_usa_sufixo_feminino(self):
        with pytest.raises(ValueError, match="não pode ser negativa"):
            validar_nao_negativo(-1, "Capacidade", feminino=True)

    def test_permite_none_por_padrao(self):
        validar_nao_negativo(None, "Quantidade")  # não levanta

    def test_rejeita_none_quando_nao_permitido(self):
        with pytest.raises(ValueError, match="não pode ser negativo"):
            validar_nao_negativo(None, "Quantidade", permitir_none=False)


class TestValidarPositivo:
    def test_aceita_positivo(self):
        validar_positivo(1, "Quantidade")  # não levanta

    def test_rejeita_zero(self):
        with pytest.raises(ValueError, match="deve ser maior que zero"):
            validar_positivo(0, "Quantidade")

    def test_rejeita_negativo(self):
        with pytest.raises(ValueError, match="deve ser maior que zero"):
            validar_positivo(-5, "Quantidade")

    def test_rejeita_none(self):
        with pytest.raises(ValueError, match="deve ser maior que zero"):
            validar_positivo(None, "Quantidade")
