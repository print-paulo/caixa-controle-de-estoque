import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QTableView, QVBoxLayout, QWidget,
)

from services.buscar_produto import (
    buscar_por_nome,
    buscar_capacidade_exposicao_por_id,
    buscar_categoria_por_id,
    buscar_estoque_deposito_por_id,
    buscar_estoque_exposicao_por_id,
    buscar_estoque_minimo_por_id,
    listar_categorias,
    listar_inativos,
    listar_todos,
)
from services.cadastrar_produto import cadastrar_produto_completo
from services.editar_produto import (
    editar_categoria,
    editar_codigo_barras,
    editar_medida_embalagem,
    editar_nome_produto,
    editar_unidade,
    editar_valor_unitario,
)
from services.estoque import ajustar_capacidade_exposicao, ajustar_estoque_minimo
from services.excluir_produto import excluir_produto, reativar_produto


COLUNAS = ["Id", "Nome", "Código de barras", "Medida", "Unidade", "Preço venda", "Custo"]


class ProdutoTableModel(QAbstractTableModel):
    """Adapta uma lista de `models.produto.Produto` pra uma QTableView."""

    def __init__(self, produtos=None):
        super().__init__()
        self._produtos = produtos or []

    def set_produtos(self, produtos):
        self.beginResetModel()
        self._produtos = produtos
        self.endResetModel()

    def produto_na_linha(self, linha):
        return self._produtos[linha]

    def rowCount(self, parent=QModelIndex()):
        return len(self._produtos)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUNAS)

    def headerData(self, secao, orientacao, papel=Qt.ItemDataRole.DisplayRole):
        if papel == Qt.ItemDataRole.DisplayRole and orientacao == Qt.Orientation.Horizontal:
            return COLUNAS[secao]
        return None

    def data(self, index, papel=Qt.ItemDataRole.DisplayRole):
        if papel != Qt.ItemDataRole.DisplayRole:
            return None

        produto = self._produtos[index.row()]
        coluna = index.column()

        if coluna == 0:
            return produto.id_produto
        if coluna == 1:
            return produto.nome_produto
        if coluna == 2:
            return produto.codigo_barras or "—"
        if coluna == 3:
            return produto.medida_embalagem or "—"
        if coluna == 4:
            return produto.unidade or "—"
        if coluna == 5:
            return f"R$ {produto.valor_unitario:.2f}" if produto.valor_unitario is not None else "—"
        if coluna == 6:
            return f"R$ {produto.custo_unitario:.2f}" if produto.custo_unitario is not None else "—"
        return None


class ProdutoDialog(QDialog):
    """
    Formulário de cadastro (produto=None) ou edição (produto preenchido).

    Chama os mesmos `services/` que o terminal usa -- nenhuma regra de
    negócio nova mora aqui, só a coleta dos dados e o encaminhamento.
    """

    def __init__(self, produto=None, parent=None):
        super().__init__(parent)
        self.produto = produto
        self.setWindowTitle("Editar produto" if produto else "Novo produto")
        self.setMinimumWidth(380)

        self.campo_nome = QLineEdit()
        self.campo_categoria = QComboBox()
        self.campo_categoria.setEditable(True)
        for categoria in listar_categorias():
            self.campo_categoria.addItem(categoria.nome_categoria)

        self.campo_codigo_barras = QLineEdit()
        self.campo_medida = QLineEdit()
        self.campo_medida.setPlaceholderText("ex: 750ML, 1L")
        self.campo_unidade = QLineEdit()

        self.campo_capacidade = QSpinBox()
        self.campo_capacidade.setRange(0, 1_000_000)
        self.campo_minimo = QSpinBox()
        self.campo_minimo.setRange(0, 1_000_000)

        self.campo_valor_unitario = QDoubleSpinBox()
        self.campo_valor_unitario.setRange(0, 1_000_000)
        self.campo_valor_unitario.setPrefix("R$ ")
        self.campo_valor_unitario.setDecimals(2)

        form = QFormLayout()
        form.addRow("Nome:", self.campo_nome)
        form.addRow("Categoria:", self.campo_categoria)
        form.addRow("Código de barras:", self.campo_codigo_barras)
        form.addRow("Medida da embalagem:", self.campo_medida)
        form.addRow("Unidade:", self.campo_unidade)
        form.addRow("Capacidade de exposição:", self.campo_capacidade)
        form.addRow("Estoque mínimo:", self.campo_minimo)

        if produto is not None:
            # preço de venda só faz sentido editar num produto que já existe
            form.addRow("Preço de venda:", self.campo_valor_unitario)

            custo = produto.custo_unitario
            deposito = buscar_estoque_deposito_por_id(produto.id_produto)
            exposicao = buscar_estoque_exposicao_por_id(produto.id_produto)
            info = QLabel(
                f"Custo atual: {'R$ %.2f' % custo if custo is not None else '—'}   |   "
                f"Depósito: {deposito}   |   Exposição: {exposicao}"
            )
            info.setStyleSheet("color: #666; font-size: 11px;")
            form.addRow(info)

            self._preencher(produto)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(botoes)

        self._definir_ordem_de_tabulacao()

    def _definir_ordem_de_tabulacao(self):
        """
        Fixa explicitamente a ordem de "próximo campo" (Tab / Enter),
        pra não depender da ordem implícita do layout.
        """
        campos = [
            self.campo_nome,
            self.campo_categoria,
            self.campo_codigo_barras,
            self.campo_medida,
            self.campo_unidade,
            self.campo_capacidade,
            self.campo_minimo,
        ]
        if self.produto is not None:
            campos.append(self.campo_valor_unitario)

        for campo_atual, proximo_campo in zip(campos, campos[1:]):
            QWidget.setTabOrder(campo_atual, proximo_campo)

    def keyPressEvent(self, event):
        """
        Enter/Return move pro próximo campo em vez de tentar salvar --
        importante porque o leitor de código de barras "digita" o código
        e aperta Enter sozinho ao terminar a leitura. Sem isso, o Enter
        do leitor tentava salvar o formulário incompleto.

        Só deixa o Enter agir normalmente (ativar o botão) quando o foco
        já está em um dos botões (Salvar/Cancelar) -- ali sim é o
        comportamento esperado.
        """
        tecla_enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        foco_esta_num_botao = isinstance(self.focusWidget(), QPushButton)

        if tecla_enter and not foco_esta_num_botao:
            self.focusNextChild()
            return

        super().keyPressEvent(event)

    def _preencher(self, produto):
        self.campo_nome.setText(produto.nome_produto)

        if produto.codigo_barras:
            self.campo_codigo_barras.setText(produto.codigo_barras)
        if produto.medida_embalagem:
            self.campo_medida.setText(produto.medida_embalagem)
        if produto.unidade:
            self.campo_unidade.setText(produto.unidade)
        if produto.valor_unitario is not None:
            self.campo_valor_unitario.setValue(produto.valor_unitario)

        categoria_atual = buscar_categoria_por_id(produto.id_produto)
        if categoria_atual:
            self.campo_categoria.setCurrentText(categoria_atual)

        capacidade = buscar_capacidade_exposicao_por_id(produto.id_produto)
        minimo = buscar_estoque_minimo_por_id(produto.id_produto)
        if capacidade is not None:
            self.campo_capacidade.setValue(capacidade)
        if minimo is not None:
            self.campo_minimo.setValue(minimo)

    def _salvar(self):
        nome = self.campo_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "O nome do produto não pode ficar em branco.")
            return

        categoria = self.campo_categoria.currentText().strip() or None
        codigo_barras = self.campo_codigo_barras.text().strip() or None
        medida = self.campo_medida.text().strip() or None
        unidade = self.campo_unidade.text().strip() or None
        capacidade = self.campo_capacidade.value()
        minimo = self.campo_minimo.value()

        try:
            if self.produto is None:
                cadastrar_produto_completo(
                    nome_produto=nome,
                    nome_categoria=categoria,
                    codigo_barras=codigo_barras,
                    medida_embalagem=medida,
                    unidade=unidade,
                    capacidade_exposicao=capacidade,
                    estoque_minimo=minimo,
                )
            else:
                id_produto = self.produto.id_produto
                editar_nome_produto(id_produto, nome)
                editar_categoria(id_produto, categoria or "")
                editar_codigo_barras(id_produto, codigo_barras or "")
                editar_medida_embalagem(id_produto, medida or "")
                editar_unidade(id_produto, unidade or "")
                editar_valor_unitario(id_produto, self.campo_valor_unitario.value())

                # capacidade/mínimo são ajustados por delta por trás -- calcula
                # a diferença entre o valor atual e o que foi digitado no formulário
                capacidade_atual = buscar_capacidade_exposicao_por_id(id_produto) or 0
                minimo_atual = buscar_estoque_minimo_por_id(id_produto) or 0
                if capacidade != capacidade_atual:
                    ajustar_capacidade_exposicao(id_produto, capacidade - capacidade_atual)
                if minimo != minimo_atual:
                    ajustar_estoque_minimo(id_produto, minimo - minimo_atual)

        except ValueError as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))
            return

        self.accept()


class ProdutosView(QWidget):
    """Tela principal de Produtos: busca, tabela, cadastro/edição/exclusão/reativação."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText("Buscar por nome...")
        self.campo_busca.returnPressed.connect(self._buscar)

        self.botao_buscar = QPushButton("Buscar")
        self.botao_buscar.clicked.connect(self._buscar)
        self.botao_limpar = QPushButton("Limpar busca")
        self.botao_limpar.clicked.connect(self._recarregar)

        self.checkbox_desativados = QCheckBox("Mostrar desativados")
        self.checkbox_desativados.stateChanged.connect(self._recarregar)

        self.botao_novo = QPushButton("Novo produto")
        self.botao_novo.clicked.connect(self._novo)
        self.botao_editar = QPushButton("Editar")
        self.botao_editar.clicked.connect(self._editar)
        self.botao_excluir = QPushButton("Excluir")
        self.botao_excluir.clicked.connect(self._excluir)
        self.botao_reativar = QPushButton("Reativar")
        self.botao_reativar.clicked.connect(self._reativar)

        barra_busca = QHBoxLayout()
        barra_busca.addWidget(self.campo_busca)
        barra_busca.addWidget(self.botao_buscar)
        barra_busca.addWidget(self.botao_limpar)
        barra_busca.addWidget(self.checkbox_desativados)

        barra_acoes = QHBoxLayout()
        barra_acoes.addWidget(self.botao_novo)
        barra_acoes.addWidget(self.botao_editar)
        barra_acoes.addWidget(self.botao_excluir)
        barra_acoes.addWidget(self.botao_reativar)
        barra_acoes.addStretch()

        self.modelo = ProdutoTableModel()
        self.tabela = QTableView()
        self.tabela.setModel(self.modelo)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.doubleClicked.connect(lambda _: self._editar())

        layout = QVBoxLayout(self)
        layout.addLayout(barra_busca)
        layout.addLayout(barra_acoes)
        layout.addWidget(self.tabela)

        self._recarregar()

    def _mostrando_desativados(self):
        return self.checkbox_desativados.isChecked()

    def _recarregar(self):
        """
        Recarrega a tabela de acordo com o modo atual (ativos ou
        desativados), e ajusta quais ações fazem sentido em cada modo:
        num produto desativado não dá pra editar/excluir de novo (o
        próprio backend já bloqueia), só reativar.
        """
        self.campo_busca.clear()
        modo_desativados = self._mostrando_desativados()

        if modo_desativados:
            self.modelo.set_produtos(listar_inativos())
        else:
            self.modelo.set_produtos(listar_todos())

        self.campo_busca.setEnabled(not modo_desativados)
        self.botao_buscar.setEnabled(not modo_desativados)
        self.botao_novo.setEnabled(not modo_desativados)
        self.botao_editar.setEnabled(not modo_desativados)
        self.botao_excluir.setEnabled(not modo_desativados)
        self.botao_reativar.setEnabled(modo_desativados)

    def _buscar(self):
        termo = self.campo_busca.text().strip()
        if not termo:
            self._recarregar()
            return
        self.modelo.set_produtos(buscar_por_nome(termo))

    def _produto_selecionado(self):
        indices = self.tabela.selectionModel().selectedRows()
        if not indices:
            return None
        return self.modelo.produto_na_linha(indices[0].row())

    def _novo(self):
        dialogo = ProdutoDialog(parent=self)
        if dialogo.exec():
            self._recarregar()

    def _editar(self):
        produto = self._produto_selecionado()
        if produto is None:
            QMessageBox.information(self, "Nenhum produto selecionado", "Selecione um produto na tabela primeiro.")
            return
        dialogo = ProdutoDialog(produto=produto, parent=self)
        if dialogo.exec():
            self._recarregar()

    def _excluir(self):
        produto = self._produto_selecionado()
        if produto is None:
            QMessageBox.information(self, "Nenhum produto selecionado", "Selecione um produto na tabela primeiro.")
            return

        resposta = QMessageBox.question(
            self, "Confirmar exclusão", f"Desativar o produto '{produto.nome_produto}'?"
        )
        if resposta == QMessageBox.StandardButton.Yes:
            excluir_produto(produto.id_produto)
            self._recarregar()

    def _reativar(self):
        produto = self._produto_selecionado()
        if produto is None:
            QMessageBox.information(self, "Nenhum produto selecionado", "Selecione um produto na tabela primeiro.")
            return

        resposta = QMessageBox.question(
            self, "Confirmar reativação", f"Reativar o produto '{produto.nome_produto}'?"
        )
        if resposta == QMessageBox.StandardButton.Yes:
            reativar_produto(produto.id_produto)
            self._recarregar()