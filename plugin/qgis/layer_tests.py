project = QgsProject.instance()
entities_layer = project.mapLayersByName('entities')[0]
print(entities_layer.attributeList())
print(entities_layer.attributeDisplayName(0))
print([f for f in entities_layer.fields()])