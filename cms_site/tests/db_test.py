from django.test import TestCase
from os.path import join
from django.conf import settings
import cms_site.models as models

#playground for db optimization
class WareManagerTest(TestCase):
    fixtures=[
        join(settings.BASE_DIR, 'cms_site/tests/fixtures/test_categories.json'),
        join(settings.BASE_DIR, 'cms_site/tests/fixtures/test_filters.json'),
        join(settings.BASE_DIR, 'cms_site/tests/fixtures/test_groups.json'),
        join(settings.BASE_DIR, 'cms_site/tests/fixtures/test_wares.json'),
        join(settings.BASE_DIR, 'cms_site/tests/fixtures/test_users.json'),
    ]
    def test_main(self):
        print('START')
        
        cat = models.Category.objects.only('parameter').get(id=1)
        print(cat.parameter)