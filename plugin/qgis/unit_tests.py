import unittest

class PlantSchemaInitializationTest(unittest.TestCase):
    
    def setUp(self):
        self.project = QgsProject.instance()
    
    def tearDown(self):
        pass
    
    def verify_layer(self, layer_name):
        print(f'Checking layer {layer_name}')
        layer = self.project.mapLayersByName(layer_name)[0]
        self.assertTrue(layer.isValid())
        
    def test_regions_initialized(self):
        self.verify_layer('regions')
    
    def test_site_groups_initialized(self):
        self.verify_layer('site_groups')

    def test_sites_initialized(self):
        self.verify_layer('sites')

    def test_locations_initialized(self):
        self.verify_layer('locations')

    def test_entity_groups_initialized(self):
        self.verify_layer('entity_groups')

    def test_entities_initialized(self):
        self.verify_layer('entities')
    
    def test_contact_groups_initialized(self):
        self.verify_layer('contact_groups')

    def test_contact_roles_initialized(self):
        self.verify_layer('contact_roles')

    def test_contacts_initialized(self):
        self.verify_layer('contacts')

    def test_attachments_initialized(self):
        self.verify_layer('attachments')
    
    def test_cables_initialized(self):
        self.verify_layer('cables')

    def test_attachments_initialized(self):
        self.verify_layer('attachments')

    def test_support_structures_initialized(self):
        self.verify_layer('support_structures')
    
    def test_support_strands_initialized(self):
        self.verify_layer('support_strands')

# Tests must be passed in explicitly because main() can't find them in __console__
unittest.main(PlantSchemaInitializationTest(), exit=False)