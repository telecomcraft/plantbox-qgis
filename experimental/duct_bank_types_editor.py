import math
import json
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QDoubleSpinBox, QSpinBox, QGroupBox, QCheckBox, 
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsRectItem,
    QGraphicsSimpleTextItem, QGraphicsLineItem, QGraphicsPolygonItem, QMainWindow, 
    QPushButton, QTableWidget, QHeaderView, QTextEdit, QComboBox, QFileDialog,
    QLineEdit, QScrollArea, QAbstractItemView, QSplitter, QToolBox
)
# from qgis.PyQt.QtSvg import QSvgGenerator
from qgis.PyQt.QtCore import Qt, QRectF, QPointF
from qgis.PyQt.QtGui import QPen, QBrush, QColor, QFont, QPolygonF, QPainter
from qgis.utils import iface

class DuctBankView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene())
        self.setBackgroundBrush(QColor("#f0f0f0"))
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)

        # Toggle Sidebar overlay button
        self.btn_toggle = QPushButton("☰ Sidebar", self)
        self.btn_toggle.setCursor(Qt.ArrowCursor)
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
        self.btn_fit.setCursor(Qt.ArrowCursor)
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
        self.setWindowTitle("Duct Bank Cross-Section Generator (JSON Schema)")
        self.resize(1150, 750)
        self.setWindowFlags(Qt.Window)

        # Expanded Mock Conduit Types Database
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
        form = QFormLayout(global_widget)
        
        self.type_name = QLineEdit()
        self.type_name.setPlaceholderText("e.g. 3x2 4-inch Standard")
        
        self.cover_h = QDoubleSpinBox(); self.cover_h.setRange(1.0, 24.0); self.cover_h.setValue(3.0); self.cover_h.setSuffix(" in")
        self.cover_v = QDoubleSpinBox(); self.cover_v.setRange(1.0, 24.0); self.cover_v.setValue(3.0); self.cover_v.setSuffix(" in")
        self.clearance_dist = QDoubleSpinBox(); self.clearance_dist.setRange(0.0, 60.0); self.clearance_dist.setValue(6.0); self.clearance_dist.setSuffix(" in")
        
        self.rebar_dia = QDoubleSpinBox(); self.rebar_dia.setRange(0.1, 2.0); self.rebar_dia.setValue(0.5); self.rebar_dia.setSuffix(" in")
        self.rebar_inset = QDoubleSpinBox(); self.rebar_inset.setRange(0.1, 12.0); self.rebar_inset.setValue(2.0); self.rebar_inset.setSuffix(" in")
        
        form.addRow("Type Name:", self.type_name)
        form.addRow("Horiz Cover:", self.cover_h)
        form.addRow("Vert Cover:", self.cover_v)
        form.addRow("Clearance Zone:", self.clearance_dist)
        form.addRow("Rebar Dia (#4):", self.rebar_dia)
        form.addRow("Rebar Inset:", self.rebar_inset)
        self.toolbox.addItem(global_widget, "Global Parameters")
        
        # --- Rows Configuration Group ---
        rows_widget = QWidget()
        rows_layout = QVBoxLayout(rows_widget)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Qty", "Conduit Type", "H-Spacer (in)", "V-Spacer Above (in)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setMinimumHeight(180) # Ensure it has decent space for 4 columns
        rows_layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_add_row = QPushButton("+ Add")
        self.btn_rem_row = QPushButton("- Remove")
        self.btn_up_row = QPushButton("↑ Up")
        self.btn_down_row = QPushButton("↓ Down")
        btn_layout.addWidget(self.btn_add_row)
        btn_layout.addWidget(self.btn_rem_row)
        btn_layout.addWidget(self.btn_up_row)
        btn_layout.addWidget(self.btn_down_row)
        rows_layout.addLayout(btn_layout)
        self.toolbox.addItem(rows_widget, "Row Configurations")
        
        # --- Display Group ---
        display_widget = QWidget()
        display_layout = QVBoxLayout(display_widget)
        self.show_labels = QCheckBox("Show Conduit Numbers"); self.show_labels.setChecked(True)
        self.show_h_dims = QCheckBox("Show Horiz Dimensions"); self.show_h_dims.setChecked(True)
        self.show_v_dims = QCheckBox("Show Vert Dimensions"); self.show_v_dims.setChecked(True)
        self.show_h_clear_dims = QCheckBox("Show Horiz Clearance Dims"); self.show_h_clear_dims.setChecked(True)
        self.show_v_clear_dims = QCheckBox("Show Vert Clearance Dims"); self.show_v_clear_dims.setChecked(True)
        self.show_details = QCheckBox("Show Detail Dimensions"); self.show_details.setChecked(True)
        self.show_encasement_line = QCheckBox("Show Inner Encasement Boundary"); self.show_encasement_line.setChecked(True)
        self.show_clearance = QCheckBox("Show Clearance Zone Buffer"); self.show_clearance.setChecked(True)
        self.show_rebar = QCheckBox("Show Corner Rebar"); self.show_rebar.setChecked(True)
        
        display_layout.addWidget(self.show_labels)
        display_layout.addWidget(self.show_h_dims)
        display_layout.addWidget(self.show_v_dims)
        display_layout.addWidget(self.show_h_clear_dims)
        display_layout.addWidget(self.show_v_clear_dims)
        display_layout.addWidget(self.show_details)
        display_layout.addWidget(self.show_encasement_line)
        display_layout.addWidget(self.show_clearance)
        display_layout.addWidget(self.show_rebar)
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
        # 2. Main Sidebar Assembly (Scroll + Pinned Bottom)
        # ==========================================
        
        self.sidebar_container = QWidget()
        sidebar_vbox = QVBoxLayout(self.sidebar_container)
        sidebar_vbox.setContentsMargins(4, 4, 4, 4)

        # Scroll area for the ToolBox
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setMinimumWidth(380) # Increased to fit 4 columns comfortably
        self.sidebar_scroll.setWidget(self.toolbox)
        
        # Fixed Bottom Buttons (Always Visible)
        # export_group = QGroupBox("Export")
        # export_layout = QHBoxLayout()
        # export_layout.setContentsMargins(6, 6, 6, 6)
        # self.btn_export_svg = QPushButton("Export SVG")
        # self.btn_export_dxf = QPushButton("Export DXF")
        # export_layout.addWidget(self.btn_export_svg)
        # export_layout.addWidget(self.btn_export_dxf)
        # export_group.setLayout(export_layout)
        
        # btn_close = QPushButton("Close")
        # btn_close.clicked.connect(self.close)
        
        sidebar_vbox.addWidget(self.sidebar_scroll)
        # sidebar_vbox.addWidget(export_group)
        # sidebar_vbox.addWidget(btn_close)

        # Canvas Setup
        self.view = DuctBankView()
        
        self.splitter.addWidget(self.sidebar_container)
        self.splitter.addWidget(self.view)
        self.splitter.setSizes([380, 770])

        # ==========================================
        # 3. Connections & Initialization
        # ==========================================
        self.view.btn_toggle.clicked.connect(self.toggle_sidebar)
        
        self.type_name.textChanged.connect(self.update_drawing)
        self.cover_h.valueChanged.connect(self.update_drawing)
        self.cover_v.valueChanged.connect(self.update_drawing)
        self.clearance_dist.valueChanged.connect(self.update_drawing)
        self.rebar_dia.valueChanged.connect(self.update_drawing)
        self.rebar_inset.valueChanged.connect(self.update_drawing)
        
        self.show_labels.stateChanged.connect(self.update_drawing)
        self.show_h_dims.stateChanged.connect(self.update_drawing)
        self.show_v_dims.stateChanged.connect(self.update_drawing)
        self.show_h_clear_dims.stateChanged.connect(self.update_drawing)
        self.show_v_clear_dims.stateChanged.connect(self.update_drawing)
        self.show_details.stateChanged.connect(self.update_drawing)
        self.show_encasement_line.stateChanged.connect(self.update_drawing)
        self.show_clearance.stateChanged.connect(self.update_drawing)
        self.show_rebar.stateChanged.connect(self.update_drawing)
        
        self.btn_add_row.clicked.connect(lambda: self.add_configuration_row(2, 7, 2.0, 2.0))
        self.btn_rem_row.clicked.connect(self.remove_configuration_row)
        self.btn_up_row.clicked.connect(self.move_row_up)
        self.btn_down_row.clicked.connect(self.move_row_down)
        
        # self.btn_export_svg.clicked.connect(self.export_svg)
        # self.btn_export_dxf.clicked.connect(self.export_dxf)

        # Expand the row configuration box by default
        self.toolbox.setCurrentIndex(1)

        # Initialize with demonstration rows (ID 7 is 4", ID 5 is 2", ID 3 is 1")
        self.add_configuration_row(2, 7, 2.0, 2.0)
        self.add_configuration_row(2, 7, 2.0, 2.0)
        self.add_configuration_row(3, 5, 1.5, 2.0)

    def toggle_sidebar(self):
        is_visible = self.sidebar_container.isVisible()
        self.sidebar_container.setVisible(not is_visible)

    def add_configuration_row(self, count, conduit_type_id, h_spacer, v_spacer):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        spin_qty = QSpinBox()
        spin_qty.setRange(1, 20)
        spin_qty.setValue(count)
        spin_qty.valueChanged.connect(self.update_drawing)
        
        combo_type = QComboBox()
        for c_id, c_data in self.CONDUIT_TYPES.items():
            combo_type.addItem(c_data["name"], c_id)
            
        index = combo_type.findData(conduit_type_id)
        if index >= 0:
            combo_type.setCurrentIndex(index)
        combo_type.currentIndexChanged.connect(self.update_drawing)
        
        spin_h_spacer = QDoubleSpinBox()
        spin_h_spacer.setRange(0.0, 12.0)
        spin_h_spacer.setValue(h_spacer)
        spin_h_spacer.valueChanged.connect(self.update_drawing)
        
        spin_v_spacer = QDoubleSpinBox()
        spin_v_spacer.setRange(-24.0, 24.0)
        spin_v_spacer.setValue(v_spacer)
        spin_v_spacer.valueChanged.connect(self.update_drawing)
        
        self.table.setCellWidget(row_idx, 0, spin_qty)
        self.table.setCellWidget(row_idx, 1, combo_type)
        self.table.setCellWidget(row_idx, 2, spin_h_spacer)
        self.table.setCellWidget(row_idx, 3, spin_v_spacer)
        
        self.update_drawing()

    def remove_configuration_row(self):
        if self.table.rowCount() > 1:
            row = self.table.currentRow()
            if row < 0:
                row = self.table.rowCount() - 1
            self.table.removeRow(row)
            self.update_drawing()

    def move_row_up(self):
        row = self.table.currentRow()
        if row > 0:
            self.swap_rows(row, row - 1)
            self.table.selectRow(row - 1)

    def move_row_down(self):
        row = self.table.currentRow()
        if row >= 0 and row < self.table.rowCount() - 1:
            self.swap_rows(row, row + 1)
            self.table.selectRow(row + 1)

    def swap_rows(self, row1, row2):
        # Read values from row1
        qty1 = self.table.cellWidget(row1, 0).value()
        type1 = self.table.cellWidget(row1, 1).currentData()
        h_spacer1 = self.table.cellWidget(row1, 2).value()
        v_spacer1 = self.table.cellWidget(row1, 3).value()
        
        # Read values from row2
        qty2 = self.table.cellWidget(row2, 0).value()
        type2 = self.table.cellWidget(row2, 1).currentData()
        h_spacer2 = self.table.cellWidget(row2, 2).value()
        v_spacer2 = self.table.cellWidget(row2, 3).value()
        
        # Set values to row1
        self.table.cellWidget(row1, 0).setValue(qty2)
        idx2 = self.table.cellWidget(row1, 1).findData(type2)
        self.table.cellWidget(row1, 1).setCurrentIndex(idx2)
        self.table.cellWidget(row1, 2).setValue(h_spacer2)
        self.table.cellWidget(row1, 3).setValue(v_spacer2)
        
        # Set values to row2
        self.table.cellWidget(row2, 0).setValue(qty1)
        idx1 = self.table.cellWidget(row2, 1).findData(type1)
        self.table.cellWidget(row2, 1).setCurrentIndex(idx1)
        self.table.cellWidget(row2, 2).setValue(h_spacer1)
        self.table.cellWidget(row2, 3).setValue(v_spacer1)
        
        self.update_drawing()

    def get_json_config(self):
        """Builds the JSON payload representing the duct bank configuration."""
        rows_data = []
        for r in range(self.table.rowCount()):
            qty = self.table.cellWidget(r, 0).value()
            c_id = self.table.cellWidget(r, 1).currentData()
            h_spacer = self.table.cellWidget(r, 2).value()
            v_spacer = self.table.cellWidget(r, 3).value()
            rows_data.append({
                "qty": qty, 
                "conduit_type_id": c_id, 
                "h_spacer": h_spacer, 
                "v_spacer": v_spacer
            })
            
        return {
            "type_name": self.type_name.text(),
            "cover_h": self.cover_h.value(),
            "cover_v": self.cover_v.value(),
            "clearance": self.clearance_dist.value(),
            "rebar_dia": self.rebar_dia.value(),
            "rebar_inset": self.rebar_inset.value(),
            "rows": rows_data
        }

    def draw_dimension(self, scene, x1, y1, x2, y2, offset_dx, offset_dy, text_val, text_font):
        """Helper method to draw a schematic-style dimension line with arrows and extension lines."""
        pen = QPen(Qt.black, 1.2)
        brush = QBrush(Qt.black)
        
        ext1 = QGraphicsLineItem(x1, y1, x1 + offset_dx, y1 + offset_dy)
        ext2 = QGraphicsLineItem(x2, y2, x2 + offset_dx, y2 + offset_dy)
        ext1.setPen(pen)
        ext2.setPen(pen)
        scene.addItem(ext1)
        scene.addItem(ext2)
        
        offset_len = math.hypot(offset_dx, offset_dy)
        if offset_len == 0: return
            
        inset = 5.0
        ratio = (offset_len - inset) / offset_len if offset_len > inset else 1.0
        
        dim_x1 = x1 + offset_dx * ratio
        dim_y1 = y1 + offset_dy * ratio
        dim_x2 = x2 + offset_dx * ratio
        dim_y2 = y2 + offset_dy * ratio
        
        dim_line = QGraphicsLineItem(dim_x1, dim_y1, dim_x2, dim_y2)
        dim_line.setPen(pen)
        scene.addItem(dim_line)
        
        angle = math.atan2(dim_y2 - dim_y1, dim_x2 - dim_x1)
        arrow_size = 6.0
        arrow_angle = math.pi / 8
        
        a1_p1 = QPointF(dim_x1 + arrow_size * math.cos(angle + arrow_angle), dim_y1 + arrow_size * math.sin(angle + arrow_angle))
        a1_p2 = QPointF(dim_x1 + arrow_size * math.cos(angle - arrow_angle), dim_y1 + arrow_size * math.sin(angle - arrow_angle))
        arrow1 = QGraphicsPolygonItem(QPolygonF([QPointF(dim_x1, dim_y1), a1_p1, a1_p2]))
        arrow1.setPen(pen); arrow1.setBrush(brush)
        scene.addItem(arrow1)
        
        a2_p1 = QPointF(dim_x2 - arrow_size * math.cos(angle + arrow_angle), dim_y2 - arrow_size * math.sin(angle + arrow_angle))
        a2_p2 = QPointF(dim_x2 - arrow_size * math.cos(angle - arrow_angle), dim_y2 - arrow_size * math.sin(angle - arrow_angle))
        arrow2 = QGraphicsPolygonItem(QPolygonF([QPointF(dim_x2, dim_y2), a2_p1, a2_p2]))
        arrow2.setPen(pen); arrow2.setBrush(brush)
        scene.addItem(arrow2)
        
        text = QGraphicsSimpleTextItem(text_val)
        text.setFont(text_font)
        t_rect = text.boundingRect()
        
        cx, cy = (dim_x1 + dim_x2) / 2, (dim_y1 + dim_y2) / 2
        
        if abs(dim_x2 - dim_x1) < 0.1: # Vertical
            text.setRotation(-90)
            if offset_dx > 0: text.setPos(cx + 6, cy + t_rect.width() / 2)
            else: text.setPos(cx - t_rect.height() - 6, cy + t_rect.width() / 2)
        else: # Horizontal
            if offset_dy > 0: text.setPos(cx - t_rect.width() / 2, cy + 6)
            else: text.setPos(cx - t_rect.width() / 2, cy - t_rect.height() - 6)
                
        scene.addItem(text)

    def update_drawing(self):
        scene = self.view.scene()
        scene.clear()

        # Build config & update JSON preview
        config = self.get_json_config()
        self.json_preview.setText(json.dumps(config, indent=2))

        scale = 10.0
        cover_h = config["cover_h"] * scale
        cover_v = config["cover_v"] * scale
        clearance = config["clearance"] * scale
        
        # Calculate Dimensions
        max_inner_w = 0
        total_inner_h = 0
        row_widths = []
        
        for i, r_data in enumerate(config["rows"]):
            dia = self.CONDUIT_TYPES[r_data["conduit_type_id"]]["od"] * scale
            w = (r_data["qty"] * dia) + (max(0, r_data["qty"] - 1) * (r_data["h_spacer"] * scale))
            row_widths.append(w)
            if w > max_inner_w: max_inner_w = w
            
            # Add V-spacer spacing above (unless it's the very first top row)
            v_spacer = (r_data["v_spacer"] * scale) if i > 0 else 0
            total_inner_h += dia + v_spacer
            
        ext_w = max_inner_w + (2 * cover_h)
        ext_h = total_inner_h + (2 * cover_v)

        # Draw Clearance Zone Buffer (Red Semi-Transparent)
        if self.show_clearance.isChecked() and clearance > 0:
            clear_rect = QGraphicsRectItem(-clearance, -clearance, ext_w + 2*clearance, ext_h + 2*clearance)
            clear_rect.setBrush(QBrush(QColor(255, 0, 0, 40)))
            clear_rect.setPen(QPen(Qt.red, 1.5, Qt.DashLine))
            scene.addItem(clear_rect)

        # Draw Encasement
        encasement = QGraphicsRectItem(0, 0, ext_w, ext_h)
        encasement.setBrush(QBrush(QColor(210, 210, 210)))
        encasement.setPen(QPen(Qt.black, 2))
        scene.addItem(encasement)

        # Draw Corner Rebar
        if self.show_rebar.isChecked():
            rebar_dia = config["rebar_dia"] * scale
            rebar_inset = config["rebar_inset"] * scale
            
            rebar_pen = QPen(Qt.black, 1.0)
            rebar_brush = QBrush(QColor(50, 50, 50))
            
            # Constrain inset to not exceed half the width/height of the encasement
            inset_x = min(rebar_inset, ext_w / 2.0)
            inset_y = min(rebar_inset, ext_h / 2.0)
            
            corners = [
                (inset_x, inset_y),
                (ext_w - inset_x, inset_y),
                (inset_x, ext_h - inset_y),
                (ext_w - inset_x, ext_h - inset_y)
            ]
            
            for rx, ry in corners:
                rebar = QGraphicsEllipseItem(rx - rebar_dia/2, ry - rebar_dia/2, rebar_dia, rebar_dia)
                rebar.setPen(rebar_pen)
                rebar.setBrush(rebar_brush)
                scene.addItem(rebar)

        # Draw Inner Encasement Boundary (Dashed Outline marking the exact edge of conduits/spacers)
        if self.show_encasement_line.isChecked():
            inner_rect = QGraphicsRectItem(cover_h, cover_v, max_inner_w, total_inner_h)
            inner_pen = QPen(QColor(100, 100, 100), 1.5, Qt.DashLine)
            inner_rect.setPen(inner_pen)
            inner_rect.setBrush(QBrush(Qt.NoBrush))
            scene.addItem(inner_rect)

        # Tracking Lines
        if self.show_details.isChecked() and config["rows"]:
            track_pen = QPen(QColor(130, 130, 130), 1, Qt.DashLine)
            
            if self.show_h_dims.isChecked():
                # Draw vertical tracking lines for the widest row to keep it clean
                widest_idx = row_widths.index(max_inner_w)
                widest_row = config["rows"][widest_idx]
                dia = self.CONDUIT_TYPES[widest_row["conduit_type_id"]]["od"] * scale
                h_spacer = widest_row["h_spacer"] * scale
                
                for col in range(widest_row["qty"]):
                    vx1 = cover_h + col * (dia + h_spacer)
                    vx2 = vx1 + dia
                    
                    v_line1 = QGraphicsLineItem(vx1, 0, vx1, ext_h)
                    v_line1.setPen(track_pen)
                    scene.addItem(v_line1)
                    
                    v_line2 = QGraphicsLineItem(vx2, 0, vx2, ext_h)
                    v_line2.setPen(track_pen)
                    scene.addItem(v_line2)
                
            if self.show_v_dims.isChecked():
                # Horizontal tracking lines
                current_y = cover_v
                for i, r_data in enumerate(config["rows"]):
                    dia = self.CONDUIT_TYPES[r_data["conduit_type_id"]]["od"] * scale
                    v_spacer = (r_data["v_spacer"] * scale) if i > 0 else 0
                    
                    current_y += v_spacer
                    
                    h_line1 = QGraphicsLineItem(0, current_y, ext_w, current_y)
                    h_line1.setPen(track_pen)
                    scene.addItem(h_line1)
                    
                    current_y += dia
                    
                    h_line2 = QGraphicsLineItem(0, current_y, ext_w, current_y)
                    h_line2.setPen(track_pen)
                    scene.addItem(h_line2)

        # Draw Conduits
        conduit_pen = QPen(QColor(0, 50, 150), 1.5)
        conduit_brush = QBrush(Qt.white)
        
        current_y = cover_v
        conduit_num = 1
        
        for i, r_data in enumerate(config["rows"]):
            qty = r_data["qty"]
            dia = self.CONDUIT_TYPES[r_data["conduit_type_id"]]["od"] * scale
            h_spacer = r_data["h_spacer"] * scale
            v_spacer = (r_data["v_spacer"] * scale) if i > 0 else 0
            
            current_y += v_spacer
            
            # Center align this specific row
            start_x = cover_h + (max_inner_w - row_widths[i]) / 2
            
            for col in range(qty):
                cx = start_x + (dia / 2) + col * (dia + h_spacer)
                cy = current_y + (dia / 2)
                
                circle = QGraphicsEllipseItem(cx - dia/2, cy - dia/2, dia, dia)
                circle.setPen(conduit_pen)
                circle.setBrush(conduit_brush)
                scene.addItem(circle)
                
                if self.show_labels.isChecked():
                    text = QGraphicsSimpleTextItem(str(conduit_num))
                    font_size = max(6, int(dia * 0.3))
                    text.setFont(QFont("Segoe UI", font_size))
                    t_rect = text.boundingRect()
                    text.setPos(cx - t_rect.width()/2, cy - t_rect.height()/2)
                    scene.addItem(text)
                
                conduit_num += 1
                
            current_y += dia

        text_font = QFont("Segoe UI", 9)
        detail_font = QFont("Segoe UI", 8)
        
        # Determine dimension offset to avoid overlapping the clearance zone if visible
        dim_offset_h = max(35, clearance + 20) if self.show_clearance.isChecked() else 35
        dim_offset_v = max(35, clearance + 20) if self.show_clearance.isChecked() else 35

        # Overall Dimensions
        if self.show_h_dims.isChecked():
            self.draw_dimension(scene, 0, ext_h, ext_w, ext_h, 0, dim_offset_h, f"W: {ext_w/scale:.1f}\"", text_font)
        if self.show_v_dims.isChecked():
            self.draw_dimension(scene, 0, 0, 0, ext_h, -dim_offset_v, 0, f"H: {ext_h/scale:.1f}\"", text_font)

        # Clearance Dimensions (Aligns perfectly with the extension lines of the Overall dimensions)
        if self.show_h_clear_dims.isChecked() and clearance > 0:
            self.draw_dimension(scene, -clearance, ext_h, 0, ext_h, 0, dim_offset_h, f"{config['clearance']:.1f}\"", text_font)
            self.draw_dimension(scene, ext_w, ext_h, ext_w + clearance, ext_h, 0, dim_offset_h, f"{config['clearance']:.1f}\"", text_font)
            
        if self.show_v_clear_dims.isChecked() and clearance > 0:
            self.draw_dimension(scene, 0, -clearance, 0, 0, -dim_offset_v, 0, f"{config['clearance']:.1f}\"", text_font)
            self.draw_dimension(scene, 0, ext_h, 0, ext_h + clearance, -dim_offset_v, 0, f"{config['clearance']:.1f}\"", text_font)

        # Detail Dimensions
        if self.show_details.isChecked() and config["rows"]:
            det_offset_h = -max(25, clearance + 15) if self.show_clearance.isChecked() else -25
            det_offset_v = max(25, clearance + 15) if self.show_clearance.isChecked() else 25

            if self.show_h_dims.isChecked():
                # Top Details (Dimensioning the widest row)
                widest_idx = row_widths.index(max_inner_w)
                widest_row = config["rows"][widest_idx]
                top_dia = self.CONDUIT_TYPES[widest_row["conduit_type_id"]]["od"] * scale
                top_spacer = widest_row["h_spacer"] * scale
                top_qty = widest_row["qty"]
                
                self.draw_dimension(scene, 0, 0, cover_h, 0, 0, det_offset_h, f"{cover_h/scale:.1f}\"", detail_font)
                self.draw_dimension(scene, cover_h, 0, cover_h + top_dia, 0, 0, det_offset_h, f"{top_dia/scale:g}\"", detail_font)
                if top_qty > 1:
                    self.draw_dimension(scene, cover_h + top_dia, 0, cover_h + top_dia + top_spacer, 0, 0, det_offset_h, f"{top_spacer/scale:g}\"", detail_font)
                
            if self.show_v_dims.isChecked():
                # Right Details (Vertical pacing for all rows)
                self.draw_dimension(scene, ext_w, 0, ext_w, cover_v, det_offset_v, 0, f"{cover_v/scale:.1f}\"", detail_font)
                curr_y = cover_v
                for i, r_data in enumerate(config["rows"]):
                    r_dia = self.CONDUIT_TYPES[r_data["conduit_type_id"]]["od"] * scale
                    v_spacer_val = r_data["v_spacer"]
                    v_spacer_px = v_spacer_val * scale
                    
                    if i > 0:
                        self.draw_dimension(scene, ext_w, curr_y, ext_w, curr_y + v_spacer_px, det_offset_v, 0, f"{v_spacer_val:g}\"", detail_font)
                        curr_y += v_spacer_px
                        
                    self.draw_dimension(scene, ext_w, curr_y, ext_w, curr_y + r_dia, det_offset_v, 0, f"{r_dia/scale:g}\"", detail_font)
                    curr_y += r_dia

        self.view.zoom_to_fit()

    # def export_svg(self):
    #     file_path, _ = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG Files (*.svg)")
    #     if not file_path: return

    #     generator = QSvgGenerator()
    #     generator.setFileName(file_path)
    #     generator.setSize(self.view.sceneRect().size().toSize())
    #     generator.setViewBox(self.view.sceneRect())
    #     generator.setTitle("Duct Bank Cross Section")

    #     painter = QPainter(generator)
    #     self.view.scene().render(painter)
    #     painter.end()

    # def export_dxf(self):
    #     file_path, _ = QFileDialog.getSaveFileName(self, "Save DXF", "", "DXF Files (*.dxf)")
    #     if not file_path: return

    #     scene = self.view.scene()
        
    #     # Internally generate DXF formatting based on the actively drawn shapes
    #     with open(file_path, 'w') as f:
    #         f.write("0\nSECTION\n2\nENTITIES\n")
            
    #         for item in scene.items():
    #             # Encasements & Clearance Zones (Rectangle -> Closed Polyline)
    #             if isinstance(item, QGraphicsRectItem):
    #                 r = item.rect()
    #                 x, y, w, h = r.x(), r.y(), r.width(), r.height()
    #                 f.write("0\nLWPOLYLINE\n8\n0\n90\n4\n70\n1\n")
                    
    #                 # Apply red color if it's the clearance zone buffer
    #                 if item.pen().color() == Qt.red or item.pen().color().name() == "#ff0000":
    #                     f.write("62\n1\n")

    #                 for px, py in [(x,y), (x+w,y), (x+w,y+h), (x,y+h)]:
    #                     f.write(f"10\n{px:.4f}\n20\n{-py:.4f}\n")
                        
    #             # Dimension/Tracking Lines (Line -> LINE)
    #             elif isinstance(item, QGraphicsLineItem):
    #                 l = item.line()
    #                 f.write("0\nLINE\n8\n0\n")
    #                 f.write(f"10\n{l.x1():.4f}\n20\n{-l.y1():.4f}\n")
    #                 f.write(f"11\n{l.x2():.4f}\n21\n{-l.y2():.4f}\n")
                    
    #             # Conduits (Ellipse -> CIRCLE)
    #             elif isinstance(item, QGraphicsEllipseItem):
    #                 r = item.rect()
    #                 cx, cy = r.center().x(), r.center().y()
    #                 rad = r.width() / 2.0
    #                 f.write("0\nCIRCLE\n8\n0\n")
    #                 f.write(f"10\n{cx:.4f}\n20\n{-cy:.4f}\n40\n{rad:.4f}\n")
                    
    #             # Dimension Arrows (Polygon -> Closed Polyline)
    #             elif isinstance(item, QGraphicsPolygonItem):
    #                 poly = item.polygon()
    #                 f.write(f"0\nLWPOLYLINE\n8\n0\n90\n{poly.count()}\n70\n1\n")
    #                 for i in range(poly.count()):
    #                     pt = poly.at(i)
    #                     f.write(f"10\n{pt.x():.4f}\n20\n{-pt.y():.4f}\n")
                        
    #             # Text Labels (SimpleTextItem -> TEXT)
    #             elif isinstance(item, QGraphicsSimpleTextItem):
    #                 text = item.text()
    #                 pos = item.scenePos()
    #                 rot = -item.rotation()  # QGraphicsItem rot is CW, DXF is CCW
    #                 font_size = item.font().pointSizeF()
    #                 if font_size <= 0: font_size = 8.0
                    
    #                 f.write("0\nTEXT\n8\n0\n")
    #                 f.write(f"10\n{pos.x():.4f}\n20\n{-pos.y():.4f}\n")
    #                 f.write(f"40\n{font_size:.4f}\n1\n{text}\n50\n{rot:.4f}\n")

    #         f.write("0\nENDSEC\n0\nEOF\n")

# Execution logic for QGIS Python Console
window = DuctBankWindow(iface.mainWindow())
window.show()