import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QMainWindow, QTabWidget
from interface.gui.placeholder_view import PlaceholderView
from interface.gui.produtos_view import ProdutosView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Caixa & Controle de Estoque")
        self.resize(1000, 650)

        abas = QTabWidget()
        abas.addTab(ProdutosView(), "Produtos")
        abas.addTab(PlaceholderView("Vendas"), "Vendas")
        abas.addTab(PlaceholderView("Compras"), "Compras")
        abas.addTab(PlaceholderView("Estoque"), "Estoque")
        abas.addTab(PlaceholderView("Relatórios"), "Relatórios")

        self.setCentralWidget(abas)