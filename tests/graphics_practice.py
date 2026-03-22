import math
import json
from qgis.PyQt.QtWidgets import (QGraphicsScene)

class DuctBankWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Graphics Test")
        self.resize(750, 500)
        self.setWindowFlags(Qt.Window)

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

window = DuctBankWindow(iface.mainWindow())
window.show()