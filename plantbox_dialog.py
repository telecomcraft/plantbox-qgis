from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel

class PlantBoxDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PlantBox Dialog")
        self.resize(300, 100)
        
        layout = QVBoxLayout(self)
        label = QLabel("PlantBox Plugin Loaded Successfully!")
        layout.addWidget(label)