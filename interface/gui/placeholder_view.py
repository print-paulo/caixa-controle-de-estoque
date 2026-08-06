from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderView(QWidget):
    """Tela temporária pra módulos que ainda não foram construídos no GUI."""

    def __init__(self, titulo, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        label = QLabel(f"{titulo}\n\n(tela ainda não construída -- disponível hoje só via terminal)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 15px;")
        layout.addWidget(label)