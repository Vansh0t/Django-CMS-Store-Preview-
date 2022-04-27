from unicodedata import name
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.models.pluginmodel import CMSPlugin
from django.db import models
from cms_site.models import Ware
from django.utils.translation import gettext_lazy as _

class CMSWare(CMSPlugin):
    ware = models.ForeignKey(Ware, on_delete=models.CASCADE)
    def __str__(self):
        return self.ware.title

@plugin_pool.register_plugin
class WarePreviewPlugin(CMSPluginBase):
    cache = False
    model = CMSWare
    render_template = "components/ware-preview.html"
    name= 'Ware Preview'
    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        return context