# Checks all cable endpoints to ensure they end in closures
# Todo: check vertex intersections with attachments

project = QgsProject.instance()
canvas = iface.mapCanvas()
cables_layer = project.mapLayersByName('Cables')[0]
print(f"Using layer {cables_layer.name()}")

# Create temp cable_endpoints layer

# Get all as-built feeder cables
# TODO: Add parameters for other combinations
expr = QgsExpression()
cables_layer.selectByExpression("type_id = 4 and status_id = 1")
cables = [cable for cable in cables_layer.getSelectedFeatures()]

cable_points = []
for cable in cables:
    geom = cable.geometry()
    line = geom.asPolyline()
    print({'cable_id': cable.id(), 'first_point': line[0], 'last_point': line[-1], 'length': round(geom.length())})