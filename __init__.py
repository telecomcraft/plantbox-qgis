def classFactory(iface):
    """Load PlantBox class from module plantbox.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .plantbox import PlantBox
    return PlantBox(iface)