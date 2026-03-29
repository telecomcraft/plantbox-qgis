import math
import json
# from qgis.PyQt.QtWidgets import (QGraphicsScene)

class DuctBankView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene())
        self.setBackgroundBrush(QColor("#f0f0f0"))
        # self.setDragMode(QGraphicsView.ScrollHandDrag)
        # self.setRenderHint(QPainter.Antialiasing)

        # Toggle Sidebar overlay button
        self.btn_toggle = QPushButton("☰ Sidebar", self)
        # self.btn_toggle.setCursor(Qt.ArrowCursor)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 220);
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 255);
                border: 1px solid #666;
            }
        """)

        # Zoom to Fit overlay button
        self.btn_fit = QPushButton("Zoom to Fit", self)
        # self.btn_fit.setCursor(Qt.ArrowCursor)
        self.btn_fit.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 220);
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 255);
                border: 1px solid #666;
            }
        """)
        self.btn_fit.clicked.connect(self.zoom_to_fit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep the buttons positioned at the top corners
        btn_fit_size = self.btn_fit.sizeHint()
        self.btn_fit.setGeometry(self.width() - btn_fit_size.width() - 15, 15, btn_fit_size.width(), btn_fit_size.height())
        
        btn_toggle_size = self.btn_toggle.sizeHint()
        self.btn_toggle.setGeometry(15, 15, btn_toggle_size.width(), btn_toggle_size.height())

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def zoom_to_fit(self):
        if self.scene() and not self.scene().itemsBoundingRect().isEmpty():
            rect = self.scene().itemsBoundingRect().adjusted(-80, -80, 80, 80)
            self.setSceneRect(rect)
            self.fitInView(rect, Qt.KeepAspectRatio)


class DuctBankWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Graphics Test")
        self.resize(750, 500)
        # self.setWindowFlags(Qt.Window) TODO: Update enum

        # Main Layout
        central_widget = DuctBankView()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

# iface imported automatically?
window = DuctBankWindow(iface.mainWindow())
window.show()