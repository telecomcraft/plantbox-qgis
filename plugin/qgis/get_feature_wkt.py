# Converts a single selected feature to its WKT encoding

layer = iface.activeLayer()
print(f"Using layer {layer.name()}")
if len(layer.selectedFeatures()) > 1:
    print(f"Too many features selected: {layer.selectedFeatures()}")
else:
    feature = layer.selectedFeatures()[0]
    print(f"Using feature {feature.id()}")
    wkt = feature.geometry().asWkt()
    print(wkt)