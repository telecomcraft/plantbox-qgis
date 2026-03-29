from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.PyQt.QtGui import QIcon

class PlantboxTools:
    def __init__(self, iface):
        self.iface = iface
        self.toolbar = None
        self.action = None

    def initGui(self):
        # Create a new toolbar
        self.toolbar = self.iface.addToolBar("Plantbox Tools")
        self.toolbar.setObjectName("PlantboxTools")

        # Create an action (button)
        self.action = QAction(QIcon(":/plugins/test_tools/icon.png"), "Do Something", self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        # Add the action to the toolbar
        self.toolbar.addAction(self.action)

    def unload(self):
        # Remove the toolbar and action when the plugin is unloaded
        if self.toolbar:
            self.iface.removeToolBar(self.toolbar)
        if self.action:
            self.iface.removePluginMenu("&Plantbox Tools", self.action)

    def run(self):
        # This function is executed when the toolbar button is clicked
        self.iface.messageBar().pushMessage("Info", "Button clicked!", level=0)