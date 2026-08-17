import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent).parent)

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit,
    QMessageBox, QPushButton, QRadioButton, QSpinBox, QStackedWidget,
    QTableView, QTabWidget, QVBoxLayout, QWidget,
)

from services.buscar_produto import buscar_por_codigo_barras
from services.registrar_compra import (
    adicionar_item_compra,
    calcular_total_compra,
    cancelar_compra,
    finalizar_compra,
    iniciar_compra,
)
from services.buscar_compra import listar_itens_compra, listar_compras
from gui.produtos_view import ProdutoDialog


COLUNAS_ITEM = ["Produto", "Qtd", "Custo unit.", "Subtotal", "Preço venda", "Lucro/un."]
COLUNAS_COMPRA = ["Id", "Data/Hora", "Fornecedor", "Total", "Status"]


class ItemCompraTableModel(QAbstractTableModel):
    """Adapta uma lista de `models.item_compra.ItemCompra` pra uma QTableView."""

    def __init__(self, itens=None):
        super().__init__()
        self._itens = itens or []

    def set_itens(self, itens):
        self.beginResetModel()
        self._itens = itens
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._itens)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUNAS_ITEM)

    def headerData(self, secao, orientacao, papel=Qt.ItemDataRole.DisplayRole):
        if papel == Qt.ItemDataRole.DisplayRole and orientacao == Qt.Orientation.Horizontal:
            return COLUNAS_ITEM[secao]
        return None

    def data(self, index, papel=Qt.ItemDataRole.DisplayRole):
        if papel != Qt.ItemDataRole.DisplayRole:
            return None

        item = self._itens[index.row()]
        coluna = index.column()

        if coluna == 0:
            return item.nome_produto
        if coluna == 1:
            return item.quantidade
        if coluna == 2:
            return f"R$ {item.valor_custo_unitario:.2f}"
        if coluna == 3:
            return f"R$ {item.sub_total:.2f}"
        if coluna == 4:
            return f"R$ {item.valor_venda_calculado:.2f}"
        if coluna == 5:
            return f"R$ {item.valor_venda_calculado - item.valor_custo_unitario:.2f}"
        return None


class CompraTableModel(QAbstractTableModel):
    """
    Adapta uma lista de `models.compra.Compra` pra uma QTableView.

    O total não é um campo de `Compra` (diferente de `Venda.valor_total`,
    que é congelado na finalização) -- por isso é calculado on-the-fly
    por linha. Tranquilo pro volume de dados de um comércio pequeno; se
    um dia a lista de compras ficar enorme, vale considerar cachear.
    """

    def __init__(self, compras=None):
        super().__init__()
        self._compras = compras or []

    def set_compras(self, compras):
        self.beginResetModel()
        self._compras = compras
        self.endResetModel()

    def compra_na_linha(self, linha):
        return self._compras[linha]

    def rowCount(self, parent=QModelIndex()):
        return len(self._compras)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUNAS_COMPRA)

    def headerData(self, secao, orientacao, papel=Qt.ItemDataRole.DisplayRole):
        if papel == Qt.ItemDataRole.DisplayRole and orientacao == Qt.Orientation.Horizontal:
            return COLUNAS_COMPRA[secao]
        return None

    def data(self, index, papel=Qt.ItemDataRole.DisplayRole):
        if papel != Qt.ItemDataRole.DisplayRole:
            return None

        compra = self._compras[index.row()]
        coluna = index.column()

        if coluna == 0:
            return compra.id_compra
        if coluna == 1:
            return compra.data_hora
        if coluna == 2:
            return compra.fornecedor or "—"
        if coluna == 3:
            return f"R$ {calcular_total_compra(compra.id_compra):.2f}"
        if coluna == 4:
            return compra.status
        return None


class ItemCompraFormDialog(QDialog):
    """
    Pergunta quantidade + custo unitário + margem de lucro pra um item de
    compra. O custo pode ser informado direto, ou calculado a partir do
    preço pago pela caixa/pacote e quantas unidades vêm nela -- mesma
    opção que já existe no terminal.
    """

    def __init__(self, nome_produto, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Comprar: {nome_produto}")
        self.setMinimumWidth(360)

        self.campo_quantidade = QSpinBox()
        self.campo_quantidade.setRange(1, 1_000_000)

        self.radio_direto = QRadioButton("Informar custo por unidade direto")
        self.radio_caixa = QRadioButton("Calcular a partir do preço da caixa/pacote")
        self.radio_direto.setChecked(True)
        self.radio_direto.toggled.connect(self._alternar_modo_custo)

        self.campo_custo_direto = QDoubleSpinBox()
        self.campo_custo_direto.setRange(0, 1_000_000)
        self.campo_custo_direto.setDecimals(4)
        self.campo_custo_direto.setPrefix("R$ ")

        self.campo_preco_caixa = QDoubleSpinBox()
        self.campo_preco_caixa.setRange(0, 1_000_000)
        self.campo_preco_caixa.setDecimals(2)
        self.campo_preco_caixa.setPrefix("R$ ")
        self.campo_unidades_caixa = QSpinBox()
        self.campo_unidades_caixa.setRange(1, 1_000_000)
        self.campo_unidades_caixa.setValue(1)

        self.campo_margem = QDoubleSpinBox()
        self.campo_margem.setRange(0, 1000)
        self.campo_margem.setDecimals(1)
        self.campo_margem.setSuffix(" %")
        self.campo_margem.setValue(30.0)

        form = QFormLayout()
        form.addRow("Quantidade comprada:", self.campo_quantidade)
        form.addRow(self.radio_direto)
        form.addRow("Custo por unidade:", self.campo_custo_direto)
        form.addRow(self.radio_caixa)
        form.addRow("Preço da caixa/pacote:", self.campo_preco_caixa)
        form.addRow("Unidades na caixa/pacote:", self.campo_unidades_caixa)
        form.addRow("Margem de lucro:", self.campo_margem)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(botoes)

        self._alternar_modo_custo()

    def _alternar_modo_custo(self):
        modo_direto = self.radio_direto.isChecked()
        self.campo_custo_direto.setEnabled(modo_direto)
        self.campo_preco_caixa.setEnabled(not modo_direto)
        self.campo_unidades_caixa.setEnabled(not modo_direto)

    def valores(self):
        """Retorna (quantidade, custo_unitario, margem_fracao) já calculados."""
        quantidade = self.campo_quantidade.value()
        margem_fracao = self.campo_margem.value() / 100

        if self.radio_direto.isChecked():
            custo_unitario = self.campo_custo_direto.value()
        else:
            custo_unitario = self.campo_preco_caixa.value() / self.campo_unidades_caixa.value()

        return quantidade, custo_unitario, margem_fracao


class DetalheCompraDialog(QDialog):
    """Mostra os dados de uma compra já registrada e a lista de itens (só leitura)."""

    def __init__(self, compra, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Compra #{compra.id_compra}")
        self.setMinimumSize(560, 320)

        total = calcular_total_compra(compra.id_compra)
        info = QLabel(
            f"Data: {compra.data_hora}   |   Fornecedor: {compra.fornecedor or '—'}   |   "
            f"Total (custo): R$ {total:.2f}   |   Status: {compra.status}"
        )
        info.setWordWrap(True)

        modelo = ItemCompraTableModel(listar_itens_compra(compra.id_compra))
        tabela = QTableView()
        tabela.setModel(modelo)
        tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.rejected.connect(self.reject)
        botoes.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(tabela)
        layout.addWidget(botoes)


class NovaCompraWidget(QWidget):
    """
    Tela de recebimento de mercadoria, no mesmo padrão da tela de Nova
    Venda: página inicial (nada em andamento) + página de compra.

    A compra só é criada no banco (`iniciar_compra()`) no momento em que
    o PRIMEIRO item é registrado com sucesso -- não ao abrir a tela nem
    ao clicar em "Abrir nova compra". O fornecedor é perguntado antes
    disso, mas fica só na memória até esse primeiro item confirmar a
    criação de verdade.
    """

    pedido_ver_historico = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.id_compra = None
        self._fornecedor_pendente = None

        self.pilha = QStackedWidget()
        self.pilha.addWidget(self._criar_pagina_inicial())
        self.pilha.addWidget(self._criar_pagina_compra())

        layout = QVBoxLayout(self)
        layout.addWidget(self.pilha)

        self._mostrar_pagina_inicial()

    def _criar_pagina_inicial(self):
        pagina = QWidget()

        texto = QLabel("Nenhuma compra em andamento.")
        texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        texto.setStyleSheet("font-size: 15px; color: #666;")

        botao_nova = QPushButton("Abrir nova compra")
        botao_nova.clicked.connect(self._abrir_pagina_de_compra)

        botao_historico = QPushButton("Ver histórico de compras")
        botao_historico.clicked.connect(self.pedido_ver_historico.emit)

        layout = QVBoxLayout(pagina)
        layout.addStretch()
        layout.addWidget(texto)
        layout.addWidget(botao_nova, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(botao_historico, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        return pagina

    def _criar_pagina_compra(self):
        pagina = QWidget()

        self.label_compra_id = QLabel()
        self.label_compra_id.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.campo_codigo = QLineEdit()
        self.campo_codigo.setPlaceholderText("Escaneie ou digite o código de barras e aperte Enter")
        self.campo_codigo.returnPressed.connect(self._ler_codigo)

        self.label_status = QLabel()
        self.label_status.setWordWrap(True)

        self.modelo_itens = ItemCompraTableModel()
        self.tabela_itens = QTableView()
        self.tabela_itens.setModel(self.modelo_itens)
        self.tabela_itens.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_itens.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabela_itens.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.label_total = QLabel()
        self.label_total.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.label_total.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.botao_finalizar = QPushButton("Finalizar compra")
        self.botao_finalizar.clicked.connect(self._finalizar)
        self.botao_cancelar = QPushButton("Cancelar")
        self.botao_cancelar.clicked.connect(self._cancelar)

        barra_botoes = QHBoxLayout()
        barra_botoes.addStretch()
        barra_botoes.addWidget(self.botao_cancelar)
        barra_botoes.addWidget(self.botao_finalizar)

        layout = QVBoxLayout(pagina)
        layout.addWidget(self.label_compra_id)
        layout.addWidget(self.campo_codigo)
        layout.addWidget(self.label_status)
        layout.addWidget(self.tabela_itens)
        layout.addWidget(self.label_total)
        layout.addLayout(barra_botoes)
        return pagina

    def _mostrar_pagina_inicial(self):
        self.id_compra = None
        self._fornecedor_pendente = None
        self.pilha.setCurrentIndex(0)

    def _abrir_pagina_de_compra(self):
        fornecedor, confirmado = QInputDialog.getText(
            self, "Fornecedor", "Nome do fornecedor (opcional):"
        )
        if not confirmado:
            return

        self._fornecedor_pendente = fornecedor.strip() or None

        rotulo_fornecedor = self._fornecedor_pendente or "não informado"
        self.label_compra_id.setText(f"Nova compra -- fornecedor: {rotulo_fornecedor} (ainda não iniciada)")
        self.botao_cancelar.setText("Voltar")
        self._limpar_status()
        self.modelo_itens.set_itens([])
        self.label_total.setText("Total (custo): R$ 0.00")
        self.botao_finalizar.setEnabled(False)
        self.pilha.setCurrentIndex(1)
        self.campo_codigo.setFocus()

    def _atualizar_itens(self):
        itens = listar_itens_compra(self.id_compra)
        self.modelo_itens.set_itens(itens)
        total = calcular_total_compra(self.id_compra)
        self.label_total.setText(f"Total (custo): R$ {total:.2f}")
        self.botao_finalizar.setEnabled(len(itens) > 0)

    def _mostrar_status(self, mensagem, erro):
        cor = "#b00020" if erro else "#1b5e20"
        self.label_status.setStyleSheet(f"color: {cor}; font-weight: bold;")
        self.label_status.setText(mensagem)

    def _limpar_status(self):
        self.label_status.setText("")

    def _ler_codigo(self):
        codigo = self.campo_codigo.text().strip()
        self.campo_codigo.clear()
        if not codigo:
            return

        produto = buscar_por_codigo_barras(codigo)
        if produto is None:
            resposta = QMessageBox.question(
                self, "Produto não encontrado",
                f"Nenhum produto ativo com o código '{codigo}'. Deseja cadastrar agora?",
            )
            if resposta != QMessageBox.StandardButton.Yes:
                return

            dialogo_cadastro = ProdutoDialog(parent=self)
            dialogo_cadastro.campo_codigo_barras.setText(codigo)
            if not dialogo_cadastro.exec():
                return

            produto = buscar_por_codigo_barras(codigo)
            if produto is None:
                self._mostrar_status("Falha ao cadastrar o produto.", erro=True)
                return

        dialogo_item = ItemCompraFormDialog(produto.nome_produto, parent=self)
        if not dialogo_item.exec():
            return
        quantidade, custo_unitario, margem = dialogo_item.valores()

        # cria a compra de verdade só agora, no primeiro item confirmado
        compra_criada_nesta_leitura = self.id_compra is None
        if compra_criada_nesta_leitura:
            self.id_compra = iniciar_compra(self._fornecedor_pendente)

        try:
            sub_total, preco_venda = adicionar_item_compra(
                self.id_compra, codigo, quantidade, custo_unitario, margem
            )
        except ValueError as e:
            self._mostrar_status(str(e), erro=True)
            if compra_criada_nesta_leitura:
                cancelar_compra(self.id_compra)
                self.id_compra = None
                rotulo_fornecedor = self._fornecedor_pendente or "não informado"
                self.label_compra_id.setText(
                    f"Nova compra -- fornecedor: {rotulo_fornecedor} (ainda não iniciada)"
                )
                self.botao_cancelar.setText("Voltar")
            return

        if compra_criada_nesta_leitura:
            rotulo_fornecedor = self._fornecedor_pendente or "não informado"
            self.label_compra_id.setText(
                f"Compra #{self.id_compra} -- fornecedor: {rotulo_fornecedor} (aberta)"
            )
            self.botao_cancelar.setText("Cancelar compra")

        lucro_unidade = preco_venda - custo_unitario
        mensagem = (
            f"Adicionado: {quantidade}x {produto.nome_produto} "
            f"(custo R$ {sub_total:.2f}, venda R$ {preco_venda:.2f}, lucro/un. R$ {lucro_unidade:.2f})"
        )
        self._mostrar_status(mensagem, erro=False)
        self._atualizar_itens()

    def _finalizar(self):
        if self.id_compra is None or self.modelo_itens.rowCount() == 0:
            QMessageBox.information(self, "Compra vazia", "Adicione ao menos um item antes de finalizar.")
            return

        try:
            total_final = finalizar_compra(self.id_compra)
        except ValueError as e:
            QMessageBox.critical(self, "Erro ao finalizar", str(e))
            return

        QMessageBox.information(
            self, "Compra finalizada",
            f"Compra #{self.id_compra} finalizada!\nTotal investido: R$ {total_final:.2f}",
        )
        self._mostrar_pagina_inicial()

    def _cancelar(self):
        if self.id_compra is None:
            self._mostrar_pagina_inicial()
            return

        resposta = QMessageBox.question(
            self, "Cancelar compra",
            f"Cancelar a compra #{self.id_compra} e retirar os itens do estoque de depósito?",
        )
        if resposta == QMessageBox.StandardButton.Yes:
            cancelar_compra(self.id_compra)
            self._mostrar_pagina_inicial()


class HistoricoComprasWidget(QWidget):
    """Lista compras já registradas, com filtro por status e detalhe de itens."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Todas", "ABERTA", "FINALIZADA", "CANCELADA"])
        self.combo_status.currentTextChanged.connect(self._recarregar)

        botao_atualizar = QPushButton("Atualizar")
        botao_atualizar.clicked.connect(self._recarregar)

        botao_ver_itens = QPushButton("Ver itens")
        botao_ver_itens.clicked.connect(self._ver_itens)

        barra = QHBoxLayout()
        barra.addWidget(QLabel("Status:"))
        barra.addWidget(self.combo_status)
        barra.addWidget(botao_atualizar)
        barra.addStretch()
        barra.addWidget(botao_ver_itens)

        self.modelo = CompraTableModel()
        self.tabela = QTableView()
        self.tabela.setModel(self.modelo)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.doubleClicked.connect(lambda _: self._ver_itens())

        layout = QVBoxLayout(self)
        layout.addLayout(barra)
        layout.addWidget(self.tabela)

        self._recarregar()

    def _recarregar(self):
        status = self.combo_status.currentText()
        if status == "Todas":
            self.modelo.set_compras(listar_compras())
        else:
            self.modelo.set_compras(listar_compras(status=status))

    def _compra_selecionada(self):
        indices = self.tabela.selectionModel().selectedRows()
        if not indices:
            return None
        return self.modelo.compra_na_linha(indices[0].row())

    def _ver_itens(self):
        compra = self._compra_selecionada()
        if compra is None:
            QMessageBox.information(self, "Nenhuma compra selecionada", "Selecione uma compra na tabela primeiro.")
            return
        dialogo = DetalheCompraDialog(compra, parent=self)
        dialogo.exec()


class ComprasView(QWidget):
    """Aba de Compras: nova compra (recebimento) e histórico, cada um como sub-aba."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.nova_compra = NovaCompraWidget()
        self.historico = HistoricoComprasWidget()

        self.abas = QTabWidget()
        self.abas.addTab(self.nova_compra, "Nova compra")
        self.abas.addTab(self.historico, "Histórico")
        self.abas.currentChanged.connect(
            lambda indice: self.historico._recarregar() if self.abas.widget(indice) is self.historico else None
        )
        self.nova_compra.pedido_ver_historico.connect(
            lambda: self.abas.setCurrentWidget(self.historico)
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.abas)