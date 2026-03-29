from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from .plantbox_dialog import PlantBoxDialog

class PlantBox:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = None
        self.action = None
        self.dialog = None

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        # For now, we will just create a basic action without an icon
        self.action = QAction("PlantBox", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        # Add to the QGIS Vector menu
        self.iface.addPluginToVectorMenu("PlantBox", self.action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        if self.action:
            self.iface.removePluginVectorMenu("PlantBox", self.action)
            del self.action

    def run(self):
        """Run method that performs all the real work."""
        # Instantiate the dialog only when the menu item is clicked
        if self.dialog is None:
            self.dialog = PlantBoxDialog(self.iface.mainWindow())
            
        self.dialog.show()
        result = self.dialog.exec_()
        
        if result:
            pass # Handle save/export logic later