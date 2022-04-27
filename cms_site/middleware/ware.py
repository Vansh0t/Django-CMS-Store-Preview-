
from cms_site.utils.endpoints import Map
from cms_site.models import Ware
from django.views.decorators.http import require_http_methods
from django.db.transaction import atomic
from cms_site.managers import CartManager, CacheManager, WareManager



class WareMiddleware:
    urls = Map()
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        processor = WareMiddleware.urls.get(request.path, None)
        if processor:
            processor(request)

        response = self.get_response(request)

        return response



def prepare_filters(request):
    c_filters = CacheManager.get_filters()
    q_filters = request.GET.getlist('f', [])
    q_filters = [f.lower() for f in q_filters]
    filters = []
    for f_name in c_filters.keys():
        if f_name.lower() in q_filters:
            filters.append(c_filters[f_name].parameter)
    return filters
def prepare_categories(request):
    c_categories = CacheManager.get_categories()
    q_categories = request.GET.getlist('c', [])
    q_categories = [c.lower() for c in q_categories]
    categories = []
    for c_name in c_categories.keys():
        if c_name.lower() in q_categories:
            categories.append(c_categories[c_name].parameter)
    return categories
def prepare_page(request):
    q_page = int(request.GET.get('p', 1))
    return q_page

@require_http_methods(['GET'])
@WareMiddleware.urls.map(['/', '/dev/data/'])
def get_wares(request):
    filters, categories, page = prepare_filters(request), prepare_categories(request), prepare_page(request)
    with atomic():
        if not request.session.session_key:
            request.session.save()
        wares = Ware.objects.apply_categories(categories).order_by(*filters).apply_page(page)
        cart = CartManager.resolve_cart(request)    
    request.data['cart'] =cart
    request.data['wares']=wares
    request.data['wares_len'] = Ware.objects.exclude(quantity=0).count()
    request.data['wares_batch'] = WareManager.ENTITIES_PER_REQUEST

@WareMiddleware.urls.map(['/ware-info/'])
def get_item_info(request):
    item_id = request.GET.get('id', None)
    try:
        request.data['ware']=Ware.objects.get(id=item_id)
    except Ware.DoesNotExist:
        request.data.update({'status':{'message':"No item id found",'is_error':True,'code':400}})













