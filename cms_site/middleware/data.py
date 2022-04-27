from warnings import filters
from cms_site.models import Filter, Category
from cms_site.managers import CacheManager
from django.core.cache import cache
from django.http import HttpResponse, HttpRequest, HttpResponsePermanentRedirect


class DataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request: HttpRequest):
        filters, categories = CacheManager.get_filters(), CacheManager.get_categories()
        #apply default data for successfull result
        #any errors and additional data provided by next middlewares 
        request.data = {'user':None,'wares':[],'filters':filters, 'categories':categories, 'status':{'message':'', 'is_error':False, 'code':200}, 'meta':{}}
        
        response = self.get_response(request)

        return response