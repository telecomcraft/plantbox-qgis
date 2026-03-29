import math
import json
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QDoubleSpinBox, QSpinBox, QGroupBox, QCheckBox, 
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsItemGroup,
    QGraphicsSimpleTextItem, QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsEllipseItem,
    QMainWindow, QPushButton, QHeaderView, QTextEdit, QComboBox, QFileDialog,
    QLineEdit, QScrollArea, QSplitter, QToolBox, QAbstractItemView
)
from qgis.PyQt.QtSvg import QSvgGenerator
from qgis.PyQt.QtCore import Qt, QPointF, QRectF
from qgis.PyQt.QtGui import QPen, QBrush, QColor, QFont, QPolygonF, QPainter
from qgis.utils import iface

class CollapsibleSection(QWidget):
    """Custom widget providing a collapsible section with a toggle button."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.btn_toggle = QPushButton(f"▼ {self.title}")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setChecked(True)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                text-align: left; font-weight: bold; padding: 6px; 
                border: 1px solid #aaa; border-radius: 3px; background-color: #e0e0e0;
            }
            QPushButton:checked { background-color: #d0d0d0; }
        """)
        self.btn_toggle.clicked.connect(self.toggle_content)
        
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(6)
        
        layout.addWidget(self.btn_toggle)
        layout.addWidget(self.content_area)

    def toggle_content(self):
        is_expanded = self.btn_toggle.isChecked()
        self.content_area.setVisible(is_expanded)
        self.btn_toggle.setText(f"▼ {self.title}" if is_expanded else f"▶ {self.title}")


class VaultView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene())
        self.setBackgroundBrush(QColor("#f0f0f0"))
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # View Selector Combo
        self.view_combo = QComboBox(self)
        self.view_combo.addItems([
            "Butterfly View", "Top View", 
            "Left Elevation", "Right Elevation", 
            "Front Elevation", "Back Elevation"
        ])
        self.view_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 230);
                border: 1px solid #aaa; border-radius: 4px;
                padding: 4px 10px; font-weight: bold; font-size: 14px;
            }
        """)

        # Overlay Buttons
        self.btn_toggle = QPushButton("☰ Sidebar", self)
        self.btn_fit = QPushButton("Zoom to Fit", self)
        
        btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 220); border: 1px solid #aaa;
                border-radius: 4px; padding: 6px 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 255); border: 1px solid #666; }
        """
        self.btn_toggle.setStyleSheet(btn_style)
        self.btn_fit.setStyleSheet(btn_style)
        self.btn_fit.clicked.connect(self.zoom_to_fit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # Center the View Combo
        vc_size = self.view_combo.sizeHint()
        self.view_combo.setGeometry((self.width() - 200) // 2, 15, 200, vc_size.height() + 10)
        
        # Corners for buttons
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


class VaultGeneratorWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Underground Structure Generator (JSON Schema)")
        self.resize(1350, 850)
        self.setWindowFlags(Qt.Window)

        # Expanded Conduit Database
        self.CONDUIT_TYPES = {
            1: {"name": '0.5" Sch 40 PVC', "od": 0.840},
            2: {"name": '0.75" Sch 40 PVC', "od": 1.050},
            3: {"name": '1" Sch 40 PVC', "od": 1.315},
            4: {"name": '1.5" Sch 40 PVC', "od": 1.900},
            5: {"name": '2" Sch 40 PVC', "od": 2.375},
            6: {"name": '3" Sch 40 PVC', "od": 3.500},
            7: {"name": '4" Sch 40 PVC', "od": 4.500},
            8: {"name": '5" Sch 40 PVC', "od": 5.563},
            9: {"name": '6" Sch 40 PVC', "od": 6.625}
        }

        self.MATERIAL_COLORS = {
            "Concrete": QColor(211, 211, 211),   
            "Polymer": QColor(220, 224, 204),    
            "Steel": QColor(176, 196, 222),      
            "Cast Iron": QColor(80, 80, 80)      
        }

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # ==========================================
        # 1. QToolBox Sections for Sidebar
        # ==========================================
        self.toolbox = QToolBox()
        
        # --- Global Parameters Group ---
        global_widget = QWidget()
        form_global = QFormLayout(global_widget)
        self.type_name = QLineEdit()
        self.type_name.setPlaceholderText("e.g. 48x48x48 Comm Vault")
        
        self.dim_l = QDoubleSpinBox(); self.dim_l.setRange(12.0, 360.0); self.dim_l.setValue(60.0); self.dim_l.setSuffix(" in")
        self.dim_w = QDoubleSpinBox(); self.dim_w.setRange(12.0, 360.0); self.dim_w.setValue(48.0); self.dim_w.setSuffix(" in")
        self.dim_h = QDoubleSpinBox(); self.dim_h.setRange(12.0, 360.0); self.dim_h.setValue(48.0); self.dim_h.setSuffix(" in")
        
        self.mat_body = QComboBox(); self.mat_body.addItems(["Concrete", "Polymer", "Steel"])
        self.mat_lid = QComboBox(); self.mat_lid.addItems(["Cast Iron", "Concrete", "Polymer", "Steel"])
        
        self.thick_wall = QDoubleSpinBox(); self.thick_wall.setRange(0.5, 24.0); self.thick_wall.setValue(4.0); self.thick_wall.setSuffix(" in")
        self.thick_floor = QDoubleSpinBox(); self.thick_floor.setRange(0.5, 24.0); self.thick_floor.setValue(6.0); self.thick_floor.setSuffix(" in")
        self.thick_lid = QDoubleSpinBox(); self.thick_lid.setRange(0.5, 24.0); self.thick_lid.setValue(6.0); self.thick_lid.setSuffix(" in")

        form_global.addRow("Structure Name:", self.type_name)
        form_global.addRow("Length (Long):", self.dim_l)
        form_global.addRow("Width (Short):", self.dim_w)
        form_global.addRow("Height:", self.dim_h)
        form_global.addRow("Body Material:", self.mat_body)
        form_global.addRow("Lid Material:", self.mat_lid)
        form_global.addRow("Wall Thickness:", self.thick_wall)
        form_global.addRow("Floor Thickness:", self.thick_floor)
        form_global.addRow("Lid Thickness:", self.thick_lid)
        self.toolbox.addItem(global_widget, "Vault Parameters")

        # --- Windows Configuration Group ---
        windows_widget = QWidget()
        windows_layout = QVBoxLayout(windows_widget)
        self.table_windows = QTableWidget(0, 6)
        self.table_windows.setHorizontalHeaderLabels(["Wall", "Window ID", "Width (in)", "Height (in)", "Top Margin", "Left Margin"])
        self.table_windows.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_windows.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_windows.setMinimumHeight(120)
        windows_layout.addWidget(self.table_windows)
        
        btn_layout_w = QHBoxLayout()
        self.btn_add_win = QPushButton("+ Add Window")
        self.btn_rem_win = QPushButton("- Remove Window")
        btn_layout_w.addWidget(self.btn_add_win)
        btn_layout_w.addWidget(self.btn_rem_win)
        windows_layout.addLayout(btn_layout_w)
        self.toolbox.addItem(windows_widget, "Wall Windows")

        # --- Openings Configuration Group ---
        openings_widget = QWidget()
        openings_layout = QVBoxLayout(openings_widget)
        self.table_openings = QTableWidget(0, 6)
        self.table_openings.setHorizontalHeaderLabels(["Win ID", "Row", "Conduit Type", "Qty", "H-Space", "V-Above"])
        self.table_openings.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_openings.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_openings.setMinimumHeight(150)
        openings_layout.addWidget(self.table_openings)
        
        btn_layout_o = QHBoxLayout()
        self.btn_add_op = QPushButton("+ Add Row")
        self.btn_rem_op = QPushButton("- Remove Row")
        self.btn_up_op = QPushButton("↑ Up")
        self.btn_down_op = QPushButton("↓ Down")
        btn_layout_o.addWidget(self.btn_add_op); btn_layout_o.addWidget(self.btn_rem_op)
        btn_layout_o.addWidget(self.btn_up_op); btn_layout_o.addWidget(self.btn_down_op)
        openings_layout.addLayout(btn_layout_o)
        self.toolbox.addItem(openings_widget, "Conduit Openings")
        
        # --- Display Group ---
        display_widget = QWidget()
        display_layout = QVBoxLayout(display_widget)
        self.show_overall_dims = QCheckBox("Show Overall Dimensions"); self.show_overall_dims.setChecked(True)
        self.show_thick_dims = QCheckBox("Show Thickness Dimensions"); self.show_thick_dims.setChecked(True)
        self.show_inner_dims = QCheckBox("Show Interior Dimensions"); self.show_inner_dims.setChecked(True)
        self.show_window_dims = QCheckBox("Show Window Dimensions"); self.show_window_dims.setChecked(True)
        self.show_hidden_lines = QCheckBox("Show Hidden Structural Lines"); self.show_hidden_lines.setChecked(True)
        self.show_view_labels = QCheckBox("Show View Perspective Labels"); self.show_view_labels.setChecked(True)
        
        display_layout.addWidget(self.show_overall_dims)
        display_layout.addWidget(self.show_thick_dims)
        display_layout.addWidget(self.show_inner_dims)
        display_layout.addWidget(self.show_window_dims)
        display_layout.addWidget(self.show_hidden_lines)
        display_layout.addWidget(self.show_view_labels)
        display_layout.addStretch()
        self.toolbox.addItem(display_widget, "Display Options")

        # --- JSON Preview ---
        json_widget = QWidget()
        json_layout = QVBoxLayout(json_widget)
        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setStyleSheet("font-family: monospace; font-size: 10px; background-color: #f8f9fa;")
        json_layout.addWidget(self.json_preview)
        self.toolbox.addItem(json_widget, "PostGIS JSON Payload Preview")

        # ==========================================
        # 2. Main Sidebar Assembly
        # ==========================================
        self.sidebar_container = QWidget()
        sidebar_vbox = QVBoxLayout(self.sidebar_container)
        sidebar_vbox.setContentsMargins(4, 4, 4, 4)

        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setMinimumWidth(400)
        self.sidebar_scroll.setWidget(self.toolbox)
        
        export_group = QGroupBox("Export")
        export_layout = QHBoxLayout()
        export_layout.setContentsMargins(6, 6, 6, 6)
        self.btn_export_svg = QPushButton("Export SVG")
        self.btn_export_dxf = QPushButton("Export DXF")
        export_layout.addWidget(self.btn_export_svg)
        export_layout.addWidget(self.btn_export_dxf)
        export_group.setLayout(export_layout)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        
        sidebar_vbox.addWidget(self.sidebar_scroll)
        sidebar_vbox.addWidget(export_group)
        sidebar_vbox.addWidget(btn_close)

        # Canvas Setup
        self.view = VaultView()
        self.splitter.addWidget(self.sidebar_container)
        self.splitter.addWidget(self.view)
        self.splitter.setSizes([400, 950])

        # ==========================================
        # 3. Connections & Initialization
        # ==========================================
        self.view.btn_toggle.clicked.connect(self.toggle_sidebar)
        self.view.view_combo.currentIndexChanged.connect(self.update_drawing)
        
        for w in [self.type_name, self.dim_l, self.dim_w, self.dim_h, self.thick_wall, self.thick_floor, self.thick_lid]:
            if isinstance(w, QLineEdit): w.textChanged.connect(self.update_drawing)
            else: w.valueChanged.connect(self.update_drawing)
            
        self.mat_body.currentIndexChanged.connect(self.update_drawing)
        self.mat_lid.currentIndexChanged.connect(self.update_drawing)
        
        for t in [self.show_overall_dims, self.show_thick_dims, self.show_inner_dims, self.show_window_dims, self.show_hidden_lines, self.show_view_labels]:
            t.stateChanged.connect(self.update_drawing)
            
        self.btn_add_win.clicked.connect(lambda: self.add_window_row("Left", "W1", 24, 24, 12, 18))
        self.btn_rem_win.clicked.connect(lambda: self.remove_table_row(self.table_windows))
        
        self.btn_add_op.clicked.connect(lambda: self.add_opening_row("W1", 1, 7, 3, 2, 2))
        self.btn_rem_op.clicked.connect(lambda: self.remove_table_row(self.table_openings))
        self.btn_up_op.clicked.connect(self.move_op_row_up)
        self.btn_down_op.clicked.connect(self.move_op_row_down)

        self.btn_export_svg.clicked.connect(self.export_svg)
        self.btn_export_dxf.clicked.connect(self.export_dxf)

        # Expand Openings by default
        self.toolbox.setCurrentIndex(2)

        # Mock Data Initialization
        self.add_window_row("Left Elevation", "WL-1", 30, 24, 8, 15)
        self.add_window_row("Front Elevation", "WF-1", 18, 18, 12, 15)
        
        # Openings for Left Window
        self.add_opening_row("WL-1", 1, 7, 4, 2, 3) # 4"
        self.add_opening_row("WL-1", 2, 7, 4, 2, 2)
        
        # Openings for Front Window
        self.add_opening_row("WF-1", 1, 5, 2, 3, 4) # 2"

        self.update_drawing()
        self.view.zoom_to_fit()

    # --- UI Helpers ---
    def toggle_sidebar(self):
        self.sidebar_container.setVisible(not self.sidebar_container.isVisible())

    def add_window_row(self, wall, w_id, w, h, t_margin, l_margin):
        row_idx = self.table_windows.rowCount()
        self.table_windows.insertRow(row_idx)
        
        combo_wall = QComboBox()
        combo_wall.addItems(["Left Elevation", "Right Elevation", "Front Elevation", "Back Elevation"])
        combo_wall.setCurrentText(wall)
        combo_wall.currentIndexChanged.connect(self.update_drawing)
        
        edit_id = QLineEdit(w_id)
        edit_id.textChanged.connect(self.update_drawing)
        
        spin_w = QDoubleSpinBox(); spin_w.setRange(1, 360); spin_w.setValue(w); spin_w.valueChanged.connect(self.update_drawing)
        spin_h = QDoubleSpinBox(); spin_h.setRange(1, 360); spin_h.setValue(h); spin_h.valueChanged.connect(self.update_drawing)
        spin_t = QDoubleSpinBox(); spin_t.setRange(0, 360); spin_t.setValue(t_margin); spin_t.valueChanged.connect(self.update_drawing)
        spin_l = QDoubleSpinBox(); spin_l.setRange(0, 360); spin_l.setValue(l_margin); spin_l.valueChanged.connect(self.update_drawing)
        
        self.table_windows.setCellWidget(row_idx, 0, combo_wall)
        self.table_windows.setCellWidget(row_idx, 1, edit_id)
        self.table_windows.setCellWidget(row_idx, 2, spin_w)
        self.table_windows.setCellWidget(row_idx, 3, spin_h)
        self.table_windows.setCellWidget(row_idx, 4, spin_t)
        self.table_windows.setCellWidget(row_idx, 5, spin_l)
        self.update_drawing()

    def add_opening_row(self, w_id, order, c_id, qty, h_space, v_space):
        row_idx = self.table_openings.rowCount()
        self.table_openings.insertRow(row_idx)
        
        edit_id = QLineEdit(w_id)
        edit_id.textChanged.connect(self.update_drawing)
        
        spin_ord = QSpinBox(); spin_ord.setRange(1, 100); spin_ord.setValue(order); spin_ord.valueChanged.connect(self.update_drawing)
        spin_qty = QSpinBox(); spin_qty.setRange(1, 20); spin_qty.setValue(qty); spin_qty.valueChanged.connect(self.update_drawing)
        
        combo_type = QComboBox()
        for key, data in self.CONDUIT_TYPES.items(): combo_type.addItem(data["name"], key)
        idx = combo_type.findData(c_id)
        if idx >= 0: combo_type.setCurrentIndex(idx)
        combo_type.currentIndexChanged.connect(self.update_drawing)
        
        spin_h = QDoubleSpinBox(); spin_h.setRange(0, 24); spin_h.setValue(h_space); spin_h.valueChanged.connect(self.update_drawing)
        spin_v = QDoubleSpinBox(); spin_v.setRange(-24, 24); spin_v.setValue(v_space); spin_v.valueChanged.connect(self.update_drawing)
        
        self.table_openings.setCellWidget(row_idx, 0, edit_id)
        self.table_openings.setCellWidget(row_idx, 1, spin_ord)
        self.table_openings.setCellWidget(row_idx, 2, combo_type)
        self.table_openings.setCellWidget(row_idx, 3, spin_qty)
        self.table_openings.setCellWidget(row_idx, 4, spin_h)
        self.table_openings.setCellWidget(row_idx, 5, spin_v)
        self.update_drawing()

    def remove_table_row(self, table):
        if table.rowCount() > 0:
            row = table.currentRow()
            table.removeRow(row if row >= 0 else table.rowCount() - 1)
            self.update_drawing()

    def move_op_row_up(self):
        row = self.table_openings.currentRow()
        if row > 0: self.swap_op_rows(row, row - 1)

    def move_op_row_down(self):
        row = self.table_openings.currentRow()
        if 0 <= row < self.table_openings.rowCount() - 1: self.swap_op_rows(row, row + 1)

    def swap_op_rows(self, r1, r2):
        for col in range(6):
            w1 = self.table_openings.cellWidget(r1, col)
            w2 = self.table_openings.cellWidget(r2, col)
            
            if isinstance(w1, QLineEdit):
                v1, v2 = w1.text(), w2.text()
                w1.setText(v2); w2.setText(v1)
            elif isinstance(w1, QComboBox):
                idx1, idx2 = w1.currentIndex(), w2.currentIndex()
                w1.setCurrentIndex(idx2); w2.setCurrentIndex(idx1)
            else:
                v1, v2 = w1.value(), w2.value()
                w1.setValue(v2); w2.setValue(v1)
        self.table_openings.selectRow(r2)
        self.update_drawing()

    # --- Data Management ---
    def get_json_config(self):
        windows = []
        for r in range(self.table_windows.rowCount()):
            windows.append({
                "wall": self.table_windows.cellWidget(r, 0).currentText(),
                "id": self.table_windows.cellWidget(r, 1).text(),
                "width": self.table_windows.cellWidget(r, 2).value(),
                "height": self.table_windows.cellWidget(r, 3).value(),
                "top": self.table_windows.cellWidget(r, 4).value(),
                "left": self.table_windows.cellWidget(r, 5).value()
            })
            
        openings = []
        for r in range(self.table_openings.rowCount()):
            openings.append({
                "window_id": self.table_openings.cellWidget(r, 0).text(),
                "order": self.table_openings.cellWidget(r, 1).value(),
                "conduit_type_id": self.table_openings.cellWidget(r, 2).currentData(),
                "qty": self.table_openings.cellWidget(r, 3).value(),
                "h_spacer": self.table_openings.cellWidget(r, 4).value(),
                "v_spacer": self.table_openings.cellWidget(r, 5).value()
            })
            
        return {
            "name": self.type_name.text(),
            "dimensions_in": {"length": self.dim_l.value(), "width": self.dim_w.value(), "height": self.dim_h.value()},
            "thickness_in": {"wall": self.thick_wall.value(), "floor": self.thick_floor.value(), "lid": self.thick_lid.value()},
            "materials": {"body": self.mat_body.currentText(), "lid": self.mat_lid.currentText()},
            "windows": windows,
            "openings": openings
        }

    # --- Graphics Drawing ---
    def draw_dimension(self, group, x1, y1, x2, y2, offset_dx, offset_dy, text_val, text_font):
        pen = QPen(Qt.black, 1.2)
        brush = QBrush(Qt.black)
        
        ext1 = QGraphicsLineItem(x1, y1, x1 + offset_dx, y1 + offset_dy)
        ext2 = QGraphicsLineItem(x2, y2, x2 + offset_dx, y2 + offset_dy)
        ext1.setPen(pen); ext2.setPen(pen)
        group.addToGroup(ext1); group.addToGroup(ext2)
        
        offset_len = math.hypot(offset_dx, offset_dy)
        if offset_len == 0: return
            
        inset = 5.0
        ratio = (offset_len - inset) / offset_len if offset_len > inset else 1.0
        dim_x1 = x1 + offset_dx * ratio; dim_y1 = y1 + offset_dy * ratio
        dim_x2 = x2 + offset_dx * ratio; dim_y2 = y2 + offset_dy * ratio
        
        dim_line = QGraphicsLineItem(dim_x1, dim_y1, dim_x2, dim_y2)
        dim_line.setPen(pen)
        group.addToGroup(dim_line)
        
        angle = math.atan2(dim_y2 - dim_y1, dim_x2 - dim_x1)
        arr_sz = 6.0; arr_ang = math.pi / 8
        
        a1_p1 = QPointF(dim_x1 + arr_sz * math.cos(angle + arr_ang), dim_y1 + arr_sz * math.sin(angle + arr_ang))
        a1_p2 = QPointF(dim_x1 + arr_sz * math.cos(angle - arr_ang), dim_y1 + arr_sz * math.sin(angle - arr_ang))
        arrow1 = QGraphicsPolygonItem(QPolygonF([QPointF(dim_x1, dim_y1), a1_p1, a1_p2]))
        arrow1.setPen(pen); arrow1.setBrush(brush)
        group.addToGroup(arrow1)
        
        a2_p1 = QPointF(dim_x2 - arr_sz * math.cos(angle + arr_ang), dim_y2 - arr_sz * math.sin(angle + arr_ang))
        a2_p2 = QPointF(dim_x2 - arr_sz * math.cos(angle - arr_ang), dim_y2 - arr_sz * math.sin(angle - arr_ang))
        arrow2 = QGraphicsPolygonItem(QPolygonF([QPointF(dim_x2, dim_y2), a2_p1, a2_p2]))
        arrow2.setPen(pen); arrow2.setBrush(brush)
        group.addToGroup(arrow2)
        
        text = QGraphicsSimpleTextItem(text_val)
        text.setFont(text_font)
        t_rect = text.boundingRect()
        
        cx, cy = (dim_x1 + dim_x2) / 2, (dim_y1 + dim_y2) / 2
        
        if abs(dim_x2 - dim_x1) < 0.1:
            text.setRotation(-90)
            text.setPos(cx + 6 if offset_dx > 0 else cx - t_rect.height() - 6, cy + t_rect.width() / 2)
        else:
            text.setPos(cx - t_rect.width() / 2, cy + 6 if offset_dy > 0 else cy - t_rect.height() - 6)
        group.addToGroup(text)

    def generate_elevation_group(self, wall_name, w, h, config, scale):
        """Creates an independent group for a wall that can be positioned/rotated"""
        group = QGraphicsItemGroup()
        c_body = self.MATERIAL_COLORS.get(config["materials"]["body"], Qt.gray)
        
        tw = config["thickness_in"]["wall"] * scale
        tf = config["thickness_in"]["floor"] * scale
        tl = config["thickness_in"]["lid"] * scale
        
        # Base Body
        rect = QGraphicsRectItem(0, 0, w, h)
        rect.setBrush(QBrush(c_body)); rect.setPen(QPen(Qt.black, 2))
        group.addToGroup(rect)
        
        # Label
        if self.show_view_labels.isChecked():
            label = QGraphicsSimpleTextItem(wall_name.upper())
            label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            label.setBrush(QBrush(QColor(50, 50, 50)))
            l_rect = label.boundingRect()
            # To ensure it stays readable when rotated in Butterfly, we don't bind it strictly here. 
            # We'll just place it relative to top edge
            label.setPos((w - l_rect.width()) / 2, -l_rect.height() - 10)
            group.addToGroup(label)
            
        # Hidden Lines
        if self.show_hidden_lines.isChecked() and w > 2*tw and h > tf + tl:
            inner_rect = QGraphicsRectItem(tw, tl, w - 2*tw, h - tl - tf)
            inner_pen = QPen(QColor(80, 80, 80), 1.5, Qt.DashLine)
            inner_rect.setPen(inner_pen); inner_rect.setBrush(QBrush(Qt.NoBrush))
            group.addToGroup(inner_rect)
            
        # Dimensional Overlay
        font_main = QFont("Segoe UI", 10)
        font_det = QFont("Segoe UI", 8)
        
        if self.show_overall_dims.isChecked():
            self.draw_dimension(group, 0, h, w, h, 0, 35, f"{w/scale:g}\"", font_main)
            self.draw_dimension(group, 0, 0, 0, h, -35, 0, f"{h/scale:g}\"", font_main)
            
        if self.show_inner_dims.isChecked() and self.show_hidden_lines.isChecked() and w > 2*tw and h > tf + tl:
            self.draw_dimension(group, tw, tl, w-tw, tl, 0, 25, f"{(w - 2*tw)/scale:g}\"", font_det)
            self.draw_dimension(group, tw, tl, tw, h-tf, 25, 0, f"{(h - tl - tf)/scale:g}\"", font_det)
            
        if self.show_thick_dims.isChecked() and self.show_hidden_lines.isChecked():
            if tl > 0: self.draw_dimension(group, w, 0, w, tl, 20, 0, f"Lid: {tl/scale:g}\"", font_det)
            if tf > 0: self.draw_dimension(group, w, h-tf, w, h, 20, 0, f"Flr: {tf/scale:g}\"", font_det)

        # Draw Windows & Openings
        win_pen = QPen(QColor(100, 100, 100), 1.5, Qt.DashLine)
        cond_pen = QPen(QColor(0, 50, 150), 1.5)
        cond_brush = QBrush(Qt.white)

        for win in config["windows"]:
            if win["wall"] != wall_name: continue
            
            wx = win["left"] * scale; wy = win["top"] * scale
            ww = win["width"] * scale; wh = win["height"] * scale
            
            w_rect = QGraphicsRectItem(wx, wy, ww, wh)
            w_rect.setPen(win_pen); w_rect.setBrush(QBrush(QColor(255, 255, 255, 30)))
            group.addToGroup(w_rect)
            
            if self.show_window_dims.isChecked():
                self.draw_dimension(group, wx, wy, wx+ww, wy, 0, -15, f"{win['width']:g}\"", font_det)
                self.draw_dimension(group, wx+ww, wy, wx+ww, wy+wh, 15, 0, f"{win['height']:g}\"", font_det)

            # Filter & Sort Openings for this Window
            ops = [o for o in config["openings"] if o["window_id"] == win["id"]]
            ops.sort(key=lambda x: x["order"])
            
            # Find max width to center everything within the window bounding box
            max_r_w = 0
            for o in ops:
                dia = self.CONDUIT_TYPES[o["conduit_type_id"]]["od"] * scale
                r_w = (o["qty"] * dia) + max(0, o["qty"] - 1) * o["h_spacer"] * scale
                if r_w > max_r_w: max_r_w = r_w
                
            curr_y = wy
            for o in ops:
                dia = self.CONDUIT_TYPES[o["conduit_type_id"]]["od"] * scale
                h_sp = o["h_spacer"] * scale
                curr_y += o["v_spacer"] * scale
                
                # Center align within the dashed window boundary
                r_w = (o["qty"] * dia) + max(0, o["qty"] - 1) * h_sp
                curr_x = wx + (ww - r_w) / 2
                
                for col in range(o["qty"]):
                    circle = QGraphicsEllipseItem(curr_x, curr_y, dia, dia)
                    circle.setPen(cond_pen); circle.setBrush(cond_brush)
                    group.addToGroup(circle)
                    curr_x += dia + h_sp
                    
                curr_y += dia

        return group

    def update_drawing(self):
        scene = self.view.scene()
        scene.clear()

        config = self.get_json_config()
        self.json_preview.setText(json.dumps(config, indent=2))

        scale = 5.0 
        L = config["dimensions_in"]["length"] * scale
        W = config["dimensions_in"]["width"] * scale
        H = config["dimensions_in"]["height"] * scale
        tw = config["thickness_in"]["wall"] * scale
        
        c_lid = self.MATERIAL_COLORS.get(config["materials"]["lid"], Qt.darkGray)
        c_body = self.MATERIAL_COLORS.get(config["materials"]["body"], Qt.gray)
        
        view_mode = self.view.view_combo.currentText()

        if view_mode == "Top View":
            group = QGraphicsItemGroup()
            rect = QGraphicsRectItem(0, 0, L, W)
            rect.setBrush(QBrush(c_lid)); rect.setPen(QPen(Qt.black, 2))
            group.addToGroup(rect)
            
            if self.show_view_labels.isChecked():
                lbl = QGraphicsSimpleTextItem("TOP VIEW (LID)")
                lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
                lbl.setPos((L - lbl.boundingRect().width()) / 2, -25)
                group.addToGroup(lbl)
                
            if self.show_hidden_lines.isChecked() and L > 2*tw and W > 2*tw:
                in_rect = QGraphicsRectItem(tw, tw, L - 2*tw, W - 2*tw)
                in_rect.setPen(QPen(QColor(80, 80, 80), 1.5, Qt.DashLine))
                group.addToGroup(in_rect)
                
            if self.show_overall_dims.isChecked():
                self.draw_dimension(group, 0, 0, L, 0, 0, -35, f"L: {L/scale:g}\"", QFont("Segoe UI", 10))
                self.draw_dimension(group, 0, 0, 0, W, -35, 0, f"W: {W/scale:g}\"", QFont("Segoe UI", 10))
                
            scene.addItem(group)

        elif view_mode in ["Left Elevation", "Right Elevation"]:
            grp = self.generate_elevation_group(view_mode, L, H, config, scale)
            scene.addItem(grp)

        elif view_mode in ["Front Elevation", "Back Elevation"]:
            grp = self.generate_elevation_group(view_mode, W, H, config, scale)
            scene.addItem(grp)

        elif view_mode == "Butterfly View":
            # Floor Center
            floor_grp = QGraphicsItemGroup()
            floor = QGraphicsRectItem(0, 0, L, W)
            floor.setBrush(QBrush(c_body)); floor.setPen(QPen(Qt.black, 2))
            floor_grp.addToGroup(floor)
            
            if self.show_view_labels.isChecked():
                lbl = QGraphicsSimpleTextItem("FLOOR")
                lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
                lbl.setBrush(QBrush(QColor(50, 50, 50)))
                l_rect = lbl.boundingRect()
                lbl.setPos((L - l_rect.width()) / 2, (W - l_rect.height()) / 2)
                floor_grp.addToGroup(lbl)
                
            if self.show_hidden_lines.isChecked() and L > 2*tw and W > 2*tw:
                in_rect = QGraphicsRectItem(tw, tw, L - 2*tw, W - 2*tw)
                in_rect.setPen(QPen(QColor(80, 80, 80), 1.5, Qt.DashLine))
                floor_grp.addToGroup(in_rect)
            scene.addItem(floor_grp)
            
            # Left Elevation (Folds UP)
            left_grp = self.generate_elevation_group("Left Elevation", L, H, config, scale)
            left_grp.setPos(0, -H)
            scene.addItem(left_grp)
            
            # Right Elevation (Folds DOWN)
            right_grp = self.generate_elevation_group("Right Elevation", L, H, config, scale)
            right_grp.setTransformOriginPoint(0, H)
            right_grp.setRotation(180)
            right_grp.setPos(L, W - H)
            scene.addItem(right_grp)
            
            # Front Elevation (Folds LEFT)
            front_grp = self.generate_elevation_group("Front Elevation", W, H, config, scale)
            front_grp.setTransformOriginPoint(0, H)
            front_grp.setRotation(90)
            front_grp.setPos(0, -H)
            scene.addItem(front_grp)
            
            # Back Elevation (Folds RIGHT)
            back_grp = self.generate_elevation_group("Back Elevation", W, H, config, scale)
            back_grp.setTransformOriginPoint(0, H)
            back_grp.setRotation(-90)
            back_grp.setPos(L, W - H)
            scene.addItem(back_grp)

        # Fit View
        rect = scene.itemsBoundingRect().adjusted(-80, -80, 80, 80)
        scene.setSceneRect(rect)
        self.view.setSceneRect(rect)


    # --- Export Engine ---
    def export_svg(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG Files (*.svg)")
        if not file_path: return

        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(self.view.sceneRect().size().toSize())
        generator.setViewBox(self.view.sceneRect())
        generator.setTitle("Underground Structure - " + self.view.view_combo.currentText())

        painter = QPainter(generator)
        self.view.scene().render(painter)
        painter.end()

    def export_dxf(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save DXF", "", "DXF Files (*.dxf)")
        if not file_path: return

        scene = self.view.scene()
        
        with open(file_path, 'w') as f:
            f.write("0\nSECTION\n2\nENTITIES\n")
            
            # Recursively export items with global coordinate mapping
            def export_item(item):
                # Map bounding primitives to global Scene coordinates (handles group rotations perfectly!)
                if isinstance(item, QGraphicsRectItem):
                    poly = item.sceneTransform().map(QPolygonF(item.rect()))
                    f.write("0\nLWPOLYLINE\n8\n0\n90\n4\n70\n1\n")
                    if item.pen().style() == Qt.DashLine: f.write("6\nDASHED\n")
                    for i in range(poly.count()):
                        f.write(f"10\n{poly.at(i).x():.4f}\n20\n{-poly.at(i).y():.4f}\n")
                        
                elif isinstance(item, QGraphicsEllipseItem):
                    c = item.sceneTransform().map(item.rect().center())
                    r = item.rect().width() / 2.0
                    f.write("0\nCIRCLE\n8\n0\n")
                    f.write(f"10\n{c.x():.4f}\n20\n{-c.y():.4f}\n40\n{r:.4f}\n")
                    
                elif isinstance(item, QGraphicsLineItem):
                    p1 = item.sceneTransform().map(item.line().p1())
                    p2 = item.sceneTransform().map(item.line().p2())
                    f.write("0\nLINE\n8\n0\n")
                    f.write(f"10\n{p1.x():.4f}\n20\n{-p1.y():.4f}\n11\n{p2.x():.4f}\n21\n{-p2.y():.4f}\n")
                    
                elif isinstance(item, QGraphicsPolygonItem):
                    poly = item.sceneTransform().map(item.polygon())
                    f.write(f"0\nLWPOLYLINE\n8\n0\n90\n{poly.count()}\n70\n1\n")
                    for i in range(poly.count()):
                        f.write(f"10\n{poly.at(i).x():.4f}\n20\n{-poly.at(i).y():.4f}\n")
                        
                elif isinstance(item, QGraphicsSimpleTextItem):
                    text = item.text()
                    pos = item.scenePos()
                    f.write("0\nTEXT\n8\n0\n")
                    f.write(f"10\n{pos.x():.4f}\n20\n{-pos.y():.4f}\n")
                    f.write(f"40\n{max(8.0, item.font().pointSizeF()):.4f}\n1\n{text}\n50\n0\n")

            # Iterate recursively through the scene tree
            for item in scene.items():
                if not isinstance(item, QGraphicsItemGroup): 
                    export_item(item)

            f.write("0\nENDSEC\n0\nEOF\n")

# Execution logic for QGIS Python Console
window = VaultGeneratorWindow(iface.mainWindow())
window.show()