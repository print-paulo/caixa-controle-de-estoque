# caixa-controle-de-estoque

Sistema de PDV (ponto de venda) e controle de estoque para mercado/mercearia, escrito em Python puro com banco SQLite.

> **Status:** backend completo, testado e funcional via terminal (CLI). **Falta a interface gráfica** (app desktop ou executável) — hoje toda a operação acontece por menus de texto no terminal, através de `main.py`.

## Funcionalidades

- **Produtos** — cadastro, edição, exclusão (soft delete/reativação), busca por nome/código de barras/id, categorias.
- **Compras** — registro com múltiplos itens, cálculo automático do preço de venda a partir do custo + margem de lucro, cancelamento com reconciliação de estoque.
- **Vendas** — registro com múltiplos itens, baixa de estoque com reposição automática do depósito para a exposição, taxa de cartão diferenciada (débito 3% / crédito 5%, recusa se ambíguo), cancelamento.
- **Estoque** — duas "gavetas" por produto (depósito e exposição, com capacidade máxima), ajuste manual, reposição manual, alerta de estoque mínimo, histórico completo de toda movimentação (`movimento_estoque`).
- **Relatórios** — produtos, estoque, vendas, compras, lucro (bruto por regime de caixa **e** lucro real com base no custo congelado em cada venda).
- **Exportação para Excel** — gera um `.xlsx` formatado (cabeçalho colorido, moeda em R$, estoque baixo destacado) com resumo executivo + uma aba por entidade, com filtro de período opcional.
- **Importação de planilha legada** (`database/importfromxlsx.py`) — migra um `Estoque.xlsx` no formato antigo pro banco novo (uso único).

## Arquitetura

```
main.py → interface/ (menus) → controllers/ (orquestração) → services/ (regras de negócio) → database/ + utils/
                                                                     ↑
                                                                 models/ (dataclasses)
```

- **`interface/`** — só menus (`print`/`input` de opção), delega tudo pro controller. Zero regra de negócio.
- **`controllers/`** — pedem dados ao usuário (`input()`), decidem a ordem das chamadas, tratam erro, imprimem resultado.
- **`services/`** — lógica de negócio pura. Regra rígida: **nenhuma função de `services/` usa `input()` ou `print()`**. Validam, calculam, gravam no banco, levantam `ValueError` em erros de validação.
- **`models/`** — uma `@dataclass` por entidade (`Produto`, `Estoque`, `Categoria`, `Venda`, `ItemVenda`, `Compra`, `ItemCompra`, `MovimentoEstoque`), convertendo `sqlite3.Row` num objeto tipado com acesso por atributo.
- **`database/`** — schema (`banco.py`) e importador da planilha legada (`importfromxlsx.py`).
- **`utils/`** — conexão com o banco (`conectar_banco.py`, já com `row_factory = sqlite3.Row`), helpers de `UPDATE` genérico (`db_campos.py`), validações (`validacoes.py`), leitor de código de barras (`leitor_barras.py`).
- **`tests_automatizados/`** — suíte `pytest` (ver abaixo).
- **`tests/`** — scripts manuais antigos, **não são testes automatizados** (chamam um controller pra teste manual no terminal).

### Decisões de design importantes

- **Transações atômicas onde importa.** `registrar_venda`, `registrar_compra` e `cadastrar_produto_completo` usam uma única conexão, um commit no final, `rollback()` em qualquer exceção — inclusive erros que já tinham produzido efeitos colaterais (como a reposição automática de estoque) antes de falhar.
- **Toda alteração de estoque é logada.** `movimento_estoque` registra venda, cancelamento, compra, reposição (automática/manual), ajuste e importação legada, via `services/estoque.py::registrar_movimento()`.
- **Produto desativado = produto excluído**, efetivamente — toda edição de produto/estoque bloqueia se `ativo = 0`, exceto o cancelamento de venda/compra, que precisa reconciliar o estoque mesmo se o produto foi desativado depois.
- **Custo vs. preço.** `produto.valor_unitario` (preço de venda) e `produto.custo_unitario` são atualizados a cada compra; cada `item_venda` congela o custo do momento (`custo_unitario_momento`), permitindo calcular o **lucro real** por venda em vez de só o lucro bruto por regime de caixa.

## Requisitos

- Python 3.10+
- Dependências em `requirements.txt` (runtime) e `requirements-dev.txt` (+ pytest, para desenvolvimento)

## Instalação

```bash
pip install -r requirements-dev.txt
```

(Use só `requirements.txt` se for apenas rodar o sistema, sem rodar os testes.)

## Como rodar

```bash
python main.py
```

Cria o banco SQLite automaticamente (`database/banco.db`) na primeira execução e abre o menu principal no terminal.

## Como rodar os testes

```bash
pytest -v
```

(ou `python -m pytest -v` se o comando `pytest` não estiver no `PATH`)

149 testes cobrindo `services/`, `utils/validacoes.py` e o importador de planilha legada, cada um rodando em um banco SQLite temporário isolado (`tests_automatizados/conftest.py`). Os controllers (que fazem `input()`/`print()`) não têm teste automatizado — a regra de negócio inteira mora em `services/`.

## Pendências conhecidas

- **Interface gráfica** — próximo passo principal. Hoje é 100% terminal.
- `Categoria` em `models/` é só um scaffold: nenhuma função de `services/` ainda devolve a linha inteira dessa entidade pra um controller consumir.
- `utils/exportar_pdf.py` — arquivo reservado pra uma futura exportação em PDF, ainda não implementado.
