from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication
from .plantbox_dialog import PlantBoxDialog

class PlantBox:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = None
        self.action = None
        self.dialog = None
        self.toolbar = None

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        
        # 1. Borrow a standard QGIS icon for our placeholder
        icon = QgsApplication.getThemeIcon('/mActionShowPluginManager.svg')
        
        # 2. Create the action that will trigger the plugin
        self.action = QAction(icon, "Open PlantBox", self.iface.mainWindow())
        self.action.setToolTip("Launch PlantBox Tools")
        self.action.triggered.connect(self.run)
        
        # 3. Add to the standard QGIS Plugins menu
        self.iface.addPluginToMenu("&PlantBox", self.action)

        # 4. Create a dedicated PlantBox toolbar
        self.toolbar = self.iface.addToolBar("PlantBox")
        self.toolbar.setObjectName("PlantBoxToolbar") # Important for QGIS saving UI state
        
        # 5. Add the action to our new toolbar
        self.toolbar.addAction(self.action)

    def unload(self):
        """Removes the plugin menu item and toolbar from QGIS GUI."""
        # Remove from menu
        if self.action:
            self.iface.removePluginMenu("&PlantBox", self.action)
            
        # Cleanly remove the toolbar
        if self.toolbar:
            self.toolbar.clear()
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar.deleteLater()
            self.toolbar = None
            
        # Clean up the action
        if self.action:
            self.action.deleteLater()
            self.action = None

    def run(self):
        """Run method that instantiates and shows the dialog."""
        # Only create the dialog if it doesn't exist yet
        if self.dialog is None:
            self.dialog = PlantBoxDialog(self.iface.mainWindow())
            
        self.dialog.show()
        result = self.dialog.exec_()
        
        if result:
            pass # We will handle save/export logic here later