import os
import sys
import unittest
from unittest.mock import MagicMock

# Add the 'plugins' directory to sys.path so 'plantbox' acts as a proper package
current_dir = os.path.dirname(os.path.abspath(__file__))
plugins_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
if plugins_dir not in sys.path:
    sys.path.insert(0, plugins_dir)

from qgis.core import QgsApplication
from plantbox.plantbox import PlantBox

qgis_app = None

def setUpModule():
    """Initializes a headless QGIS application before tests run."""
    global qgis_app
    
    prefix_path = os.environ.get('QGIS_PREFIX_PATH', 'C:\\Program Files\\QGIS 3.44.8\\apps\\qgis')
    QgsApplication.setPrefixPath(prefix_path, True)
    
    qgis_app = QgsApplication([], False)
    qgis_app.initQgis()
    print(f"\n[+] Headless QGIS booted successfully! (Prefix: {prefix_path})")

def tearDownModule():
    """Safely shuts down the QGIS environment after tests finish."""
    global qgis_app
    if qgis_app:
        qgis_app.exitQgis()
        print("[-] Headless QGIS shut down.")


class TestPlantBox(unittest.TestCase):
    
    def setUp(self):
        """Runs before EACH test. Sets up a fresh mock interface and plugin instance."""
        # A simple mock interface. No complicated return_value hacks needed yet!
        self.mock_iface = MagicMock()
        self.plugin = PlantBox(self.mock_iface)

    def test_plantbox_initialization(self):
        """
        Test 1: Does the plugin instantiate correctly?
        Verifies that the main class accepts the iface and sets default states.
        """
        self.assertEqual(self.plugin.iface, self.mock_iface)
        self.assertIsNone(self.plugin.action)
        self.assertIsNone(self.plugin.dialog)


if __name__ == '__main__':
    unittest.main()