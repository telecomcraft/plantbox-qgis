import unittest


class RattlesnakeIslandTests(unittest.TestCase):
    
    def setUp(self):
        self.project = QgsProject.instance()
    
    def tearDown(self):
        print('Torn down')
    
    def test_entities(self):
        entities_layer = self.project.mapLayersByName('entities')[0]
        entities_layer.startEditing()
        
        entity_ottawa_isp = QgsVectorLayerUtils.createFeature(entities_layer)
        entity_ottawa_isp['name'] = 'Ottawa ISP'
        entity_ottawa_isp['notes'] = "This is a test entity."
        entities_layer.addFeature(entity_ottawa_isp)
        entities_layer.commitChanges()
    
    def test_entity_groups(self):
        entity_groups_layer = self.project.mapLayersByName('entity_groups')[0]
        entity_groups_layer.startEditing()
        
        entity_groups_service_providers = QgsVectorLayerUtils.createFeature(entity_groups_layer)
        entity_groups_service_providers['name'] = 'Service Providers'
        entity_groups_layer.addFeature(entity_groups_service_providers)
        entity_groups_layer.commitChanges()
    
    def test_add_ottawa_isp_to_service_providers(self):
        pass
    
    def test_contact_groups(self):
        contact_groups_layer = self.project.mapLayersByName('contact_groups')[0]
    
    def test_contact_roles(self):
        pass
    
    def test_contacts(self):
        contacts_layer = self.project.mapLayersByName('contacts')[0]
    
    def test_regions(self):
        regions_layer = self.project.mapLayersByName('regions')[0]
        regions_layer.startEditing()
        
        region_rattlesnake_island = QgsVectorLayerUtils.createFeature(regions_layer)
        region_rattlesnake_island['name'] = 'Rattlesnake Island'
        region_rattlesnake_island['notes'] = 'A simple note.'
        island_wkt = 'Polygon ((-82.85672264705516454 41.68220000982324791, -82.85657297906330143 41.68191717010308395,'\
                     '-82.85671609094914913 41.68155765409365188, -82.85629976546292141 41.68124671970893758,'\
                     '-82.85579703585504774 41.68058401550146641, -82.85519823761394775 41.6804434655945073,'\
                     '-82.85381482271696996 41.68049204979759281, -82.85313829380186235 41.68023941154095979,'\
                     '-82.85149901219982382 41.67867173659728763, -82.85115207429463169 41.67769353990797043,'\
                     '-82.85000702538957285 41.67715271505898045, -82.84841126484364793 41.67689671969595366,'\
                     '-82.84729889518513346 41.67710564302281995, -82.84653996851761804 41.6776967789944095,'\
                     '-82.84583308253579048 41.67768382264775084, -82.84504379880138458 41.67793485177828927,'\
                     '-82.84436943824827893 41.67845634025845669, -82.84431002247603715 41.67884224333261045,'\
                     '-82.84442581565780017 41.67905070283948277, -82.84476841683915893 41.67914787298968093,'\
                     '-82.84557491991812128 41.67952314878527176, -82.84633831086011924 41.67984425740706911,'\
                     '-82.84750055284251857 41.68051148346855683, -82.84871483551070526 41.68071877559370364,'\
                     '-82.85138625738062501 41.68090015565545059, -82.85246176488672631 41.68084185497707495,'\
                     '-82.85349336944177878 41.68108432502845062, -82.8544530317574015 41.68207851135177577,'\
                     '-82.85513318675678818 41.68234793896004931, -82.85573477322979841 41.68226399429450879,'\
                     '-82.85601354169119759 41.68238032740678989, -82.85649017763036284 41.68233795442289846,'\
                     '-82.85672264705516454 41.68220000982324791))'
        region_rattlesnake_island.setGeometry(QgsGeometry.fromWkt(island_wkt))
        regions_layer.addFeature(region_rattlesnake_island)
        regions_layer.commitChanges()
        #regions_layer.stopEditing()
    
    def test_site_groups(self):
        site_groups_layer = self.project.mapLayersByName('site_groups')[0]
    
    def test_sites(self):
        sites_layer = self.project.mapLayersByName('sites')[0]
    
    def test_locations(self):
        locations_layer = self.project.mapLayersByName('locations')[0]
        
        # Create "Ottawa ISP entity

        

        # Create "Rattlesnake Island" region

        

        # Create 'Service Providers' entity group
        # Create 'Community Fiber' entity
        # Create 'Community Fiber Sites' site group
        # Create 'Community Fiber Central Office' site
        # contact groups
        # contact roles
        # contact

# Tests must be passed in explicitly because main() can't find them, and exit=True will crash QGIS!
unittest.main(RattlesnakeIslandTests(), exit=False)