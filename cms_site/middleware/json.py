import json
from django.http.request import QueryDict
from django.http import HttpResponse

class JsonParserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, req):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        try: 
            if req.content_type == 'application/json':
                if req.method == 'POST':
                    data = json.loads(req.body)
                    req.json = data
                    print(f'JSON - {req.json}')
        except:
            return HttpResponse(status=400, reson='Unable to parse json content')
        
        response = self.get_response(req)
        # Code to be executed for each request/response after
        # the view is called.

        return response