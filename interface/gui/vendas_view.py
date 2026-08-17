import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton,
    QStackedWidget, QTableView, QTabWidget, QVBoxLayout, QWidget,
)

from services.buscar_produto import buscar_por_codigo_barras
from services.registrar_venda import (
    TAXA_CARTAO_CREDITO,
    TAXA_CARTAO_DEBITO,
    adicionar_item_venda,
    calcular_total_venda,
    cancelar_venda,
    eh_pagamento_no_cartao,
    finalizar_venda,
    iniciar_venda,
    taxa_cartao,
)
from services.buscar_venda import listar_itens_venda, listar_vendas


COLUNAS_ITEM = ["Produto", "Qtd", "Preço unit.", "Subtotal"]
COLUNAS_VENDA = ["Id", "Data/Hora", "Pagamento", "Total", "Status"]


class ItemVendaTableModel(QAbstractTableModel):
    """Adapta uma lista de `models.item_venda.ItemVenda` pra uma QTableView."""

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
            return f"R$ {item.valor_unitario_momento:.2f}"
        if coluna == 3:
            return f"R$ {item.sub_total:.2f}"
        return None


class VendaTableModel(QAbstractTableModel):
    """Adapta uma lista de `models.venda.Venda` pra uma QTableView."""

    def __init__(self, vendas=None):
        super().__init__()
        self._vendas = vendas or []

    def set_vendas(self, vendas):
        self.beginResetModel()
        self._vendas = vendas
        self.endResetModel()

    def venda_na_linha(self, linha):
        return self._vendas[linha]

    def rowCount(self, parent=QModelIndex()):
        return len(self._vendas)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUNAS_VENDA)

    def headerData(self, secao, orientacao, papel=Qt.ItemDataRole.DisplayRole):
        if papel == Qt.ItemDataRole.DisplayRole and orientacao == Qt.Orientation.Horizontal:
            return COLUNAS_VENDA[secao]
        return None

    def data(self, index, papel=Qt.ItemDataRole.DisplayRole):
        if papel != Qt.ItemDataRole.DisplayRole:
            return None

        venda = self._vendas[index.row()]
        coluna = index.column()

        if coluna == 0:
            return venda.id_venda
        if coluna == 1:
            return venda.data_hora
        if coluna == 2:
            return venda.forma_pagamento or "—"
        if coluna == 3:
            return f"R$ {venda.valor_total:.2f}" if venda.valor_total is not None else "—"
        if coluna == 4:
            return venda.status
        return None


class FormaPagamentoDialog(QDialog):
    """
    Pergunta a forma de pagamento por uma lista fixa de opções, em vez de
    texto livre -- evita de vez o caso de "cartão" ambíguo (sem dizer se é
    débito ou crédito) que o terminal precisa tratar como erro.
    """

    OPCOES = ["Dinheiro", "PIX", "Cartão Débito", "Cartão Crédito"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Forma de pagamento")
        self.setMinimumWidth(260)

        self.combo = QComboBox()
        self.combo.addItems(self.OPCOES)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Como o cliente vai pagar?"))
        layout.addWidget(self.combo)
        layout.addWidget(botoes)

    def forma_pagamento(self):
        return self.combo.currentText()


class DetalheVendaDialog(QDialog):
    """Mostra os dados de uma venda já registrada e a lista de itens (só leitura)."""

    def __init__(self, venda, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Venda #{venda.id_venda}")
        self.setMinimumSize(520, 320)

        valor = f"R$ {venda.valor_total:.2f}" if venda.valor_total is not None else "—"
        info = QLabel(
            f"Data: {venda.data_hora}   |   Pagamento: {venda.forma_pagamento or '—'}   |   "
            f"Total: {valor}   |   Status: {venda.status}"
        )
        info.setWordWrap(True)

        modelo = ItemVendaTableModel(listar_itens_venda(venda.id_venda))
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


class NovaVendaWidget(QWidget):
    """
    Tela de checkout, com duas "páginas" (QStackedWidget):

    1. Página inicial -- nenhuma venda em andamento. Mostra um botão pra
       abrir uma venda nova e outro pra ir direto no histórico.
    2. Página de venda -- escanear/digitar código de barras + quantidade,
       finalizar ou cancelar.

    A venda só é criada no banco (`iniciar_venda()`) no momento em que o
    PRIMEIRO item é lido com sucesso -- não ao entrar na tela, nem ao
    clicar em "Abrir nova venda". Isso evita acumular vendas 'ABERTA'
    vazias no banco só de o usuário navegar ou cancelar sem escanear
    nada. Se essa primeira leitura falhar (ex: estoque insuficiente), a
    venda recém-criada é cancelada na hora, sem deixar sobra.
    """

    pedido_ver_historico = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.id_venda = None

        self.pilha = QStackedWidget()
        self.pilha.addWidget(self._criar_pagina_inicial())
        self.pilha.addWidget(self._criar_pagina_venda())

        layout = QVBoxLayout(self)
        layout.addWidget(self.pilha)

        self._mostrar_pagina_inicial()

    def _criar_pagina_inicial(self):
        pagina = QWidget()

        texto = QLabel("Nenhuma venda em andamento.")
        texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        texto.setStyleSheet("font-size: 15px; color: #666;")

        botao_nova = QPushButton("Abrir nova venda")
        botao_nova.clicked.connect(self._abrir_pagina_de_venda)

        botao_historico = QPushButton("Ver histórico de vendas")
        botao_historico.clicked.connect(self.pedido_ver_historico.emit)

        layout = QVBoxLayout(pagina)
        layout.addStretch()
        layout.addWidget(texto)
        layout.addWidget(botao_nova, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(botao_historico, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        return pagina

    def _criar_pagina_venda(self):
        pagina = QWidget()

        self.label_venda_id = QLabel()
        self.label_venda_id.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.campo_codigo = QLineEdit()
        self.campo_codigo.setPlaceholderText("Escaneie ou digite o código de barras e aperte Enter")
        self.campo_codigo.returnPressed.connect(self._ler_codigo)

        self.label_status = QLabel()
        self.label_status.setWordWrap(True)

        self.modelo_itens = ItemVendaTableModel()
        self.tabela_itens = QTableView()
        self.tabela_itens.setModel(self.modelo_itens)
        self.tabela_itens.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_itens.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabela_itens.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.label_total = QLabel()
        self.label_total.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.label_total.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.botao_finalizar = QPushButton("Finalizar venda")
        self.botao_finalizar.clicked.connect(self._finalizar)
        self.botao_cancelar = QPushButton("Cancelar")
        self.botao_cancelar.clicked.connect(self._cancelar)

        barra_botoes = QHBoxLayout()
        barra_botoes.addStretch()
        barra_botoes.addWidget(self.botao_cancelar)
        barra_botoes.addWidget(self.botao_finalizar)

        layout = QVBoxLayout(pagina)
        layout.addWidget(self.label_venda_id)
        layout.addWidget(self.campo_codigo)
        layout.addWidget(self.label_status)
        layout.addWidget(self.tabela_itens)
        layout.addWidget(self.label_total)
        layout.addLayout(barra_botoes)
        return pagina

    def _mostrar_pagina_inicial(self):
        self.id_venda = None
        self.pilha.setCurrentIndex(0)

    def _abrir_pagina_de_venda(self):
        """
        Só troca de tela -- NÃO cria a venda no banco ainda. A venda de
        verdade só nasce em `_ler_codigo`, no primeiro item lido com
        sucesso.
        """
        self.label_venda_id.setText("Nova venda (ainda não iniciada)")
        self.botao_cancelar.setText("Voltar")
        self._limpar_status()
        self.modelo_itens.set_itens([])
        self.label_total.setText("Total: R$ 0.00")
        self.botao_finalizar.setEnabled(False)
        self.pilha.setCurrentIndex(1)
        self.campo_codigo.setFocus()

    def _atualizar_itens(self):
        itens = listar_itens_venda(self.id_venda)
        self.modelo_itens.set_itens(itens)
        total = calcular_total_venda(self.id_venda)
        self.label_total.setText(f"Total: R$ {total:.2f}")
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
            self._mostrar_status(f"Produto não encontrado ou inativo (código: {codigo}).", erro=True)
            return

        quantidade, confirmado = QInputDialog.getInt(
            self, "Quantidade", f"Quantidade de '{produto.nome_produto}':", value=1, minValue=1
        )
        if not confirmado:
            return

        # cria a venda de verdade só agora, na primeira leitura bem-sucedida
        venda_criada_nesta_leitura = self.id_venda is None
        if venda_criada_nesta_leitura:
            self.id_venda = iniciar_venda()

        try:
            resultado = adicionar_item_venda(self.id_venda, codigo, quantidade)
        except ValueError as e:
            self._mostrar_status(str(e), erro=True)
            if venda_criada_nesta_leitura:
                # a 1a leitura falhou -- desfaz a venda que acabou de ser
                # criada, pra não deixar uma 'ABERTA' vazia pra trás
                cancelar_venda(self.id_venda)
                self.id_venda = None
                self.label_venda_id.setText("Nova venda (ainda não iniciada)")
                self.botao_cancelar.setText("Voltar")
            return

        if venda_criada_nesta_leitura:
            self.label_venda_id.setText(f"Venda #{self.id_venda} (aberta)")
            self.botao_cancelar.setText("Cancelar venda")

        mensagem = f"Adicionado: {quantidade}x {produto.nome_produto} = R$ {resultado['subtotal']:.2f}"
        if resultado["quantidade_reposta"]:
            mensagem += f"  |  Reposição automática: {resultado['quantidade_reposta']} un."
        if resultado["estoque_baixo"]:
            mensagem += "  |  ATENÇÃO: produto abaixo do estoque mínimo!"

        self._mostrar_status(mensagem, erro=False)
        self._atualizar_itens()

    def _finalizar(self):
        if self.id_venda is None or self.modelo_itens.rowCount() == 0:
            QMessageBox.information(self, "Venda vazia", "Adicione ao menos um item antes de finalizar.")
            return

        dialogo_pagamento = FormaPagamentoDialog(parent=self)
        if not dialogo_pagamento.exec():
            return

        forma_pagamento = dialogo_pagamento.forma_pagamento()
        subtotal_antes_da_taxa = calcular_total_venda(self.id_venda)

        try:
            total_final = finalizar_venda(self.id_venda, forma_pagamento)
        except ValueError as e:
            QMessageBox.critical(self, "Erro ao finalizar", str(e))
            return

        mensagem = (
            f"Venda #{self.id_venda} finalizada!\n"
            f"Forma de pagamento: {forma_pagamento}\n"
        )
        if eh_pagamento_no_cartao(forma_pagamento):
            taxa = taxa_cartao(forma_pagamento)
            mensagem += f"(Taxa de {taxa * 100:.0f}% aplicada sobre R$ {subtotal_antes_da_taxa:.2f})\n"
        mensagem += f"Total: R$ {total_final:.2f}"

        QMessageBox.information(self, "Venda finalizada", mensagem)
        self._mostrar_pagina_inicial()

    def _cancelar(self):
        if self.id_venda is None:
            # nada foi criado no banco ainda -- só volta pra tela inicial,
            # sem popup e sem chamar o backend
            self._mostrar_pagina_inicial()
            return

        resposta = QMessageBox.question(
            self, "Cancelar venda",
            f"Cancelar a venda #{self.id_venda} e devolver os itens ao estoque?",
        )
        if resposta == QMessageBox.StandardButton.Yes:
            cancelar_venda(self.id_venda)
            self._mostrar_pagina_inicial()


class HistoricoVendasWidget(QWidget):
    """Lista vendas já registradas, com filtro por status e detalhe de itens."""

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

        self.modelo = VendaTableModel()
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
            self.modelo.set_vendas(listar_vendas())
        else:
            self.modelo.set_vendas(listar_vendas(status=status))

    def _venda_selecionada(self):
        indices = self.tabela.selectionModel().selectedRows()
        if not indices:
            return None
        return self.modelo.venda_na_linha(indices[0].row())

    def _ver_itens(self):
        venda = self._venda_selecionada()
        if venda is None:
            QMessageBox.information(self, "Nenhuma venda selecionada", "Selecione uma venda na tabela primeiro.")
            return
        dialogo = DetalheVendaDialog(venda, parent=self)
        dialogo.exec()


class VendasView(QWidget):
    """Aba de Vendas: nova venda (checkout) e histórico, cada um como sub-aba."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.nova_venda = NovaVendaWidget()
        self.historico = HistoricoVendasWidget()

        self.abas = QTabWidget()
        self.abas.addTab(self.nova_venda, "Nova venda")
        self.abas.addTab(self.historico, "Histórico")
        # atualiza o histórico automaticamente sempre que a aba é aberta,
        # pra já mostrar a venda que acabou de ser finalizada
        self.abas.currentChanged.connect(
            lambda indice: self.historico._recarregar() if self.abas.widget(indice) is self.historico else None
        )
        # botão "Ver histórico de vendas" na página inicial da Nova Venda
        # pede pra essa aba trocar de verdade, em vez de só existir solto
        self.nova_venda.pedido_ver_historico.connect(
            lambda: self.abas.setCurrentWidget(self.historico)
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.abas)