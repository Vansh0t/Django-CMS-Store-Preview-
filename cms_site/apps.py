from django.apps import AppConfig

class CMSSite(AppConfig):
    name = 'cms_site'
    verbose_name = "CMS Site Base App"
    def ready(self):
        pass
