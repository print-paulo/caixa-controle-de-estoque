"""
Ponto de entrada do app desktop (PySide6).

Uso:
    python -m gui.app
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

from database.banco import criar_tabelas
from utils.conectar_banco import conectar_banco
from interface.gui.main_window import MainWindow


def main():
    # garante que o banco e as tabelas existem antes de abrir qualquer tela
    conn = conectar_banco()
    criar_tabelas(conn)
    conn.close()

    app = QApplication(sys.argv)
    app.setApplicationName("Caixa & Controle de Estoque")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()