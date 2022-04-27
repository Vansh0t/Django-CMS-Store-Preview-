from cms_site.models import Ware
from cms.models.fields import PlaceholderField



class WarePlaceholder(Ware):
    placeholder = PlaceholderField('ware_placeholder')