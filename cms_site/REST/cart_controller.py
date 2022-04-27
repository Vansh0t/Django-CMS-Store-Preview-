from django.http import HttpRequest, FileResponse, HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from cms_site.models import Cart, Ware, CartWare
from cms_site.managers import CartManager
#import socket
#
#
#def is_localhost(request):
#    print(socket.gethostbyaddr(request.META['REMOTE_ADDR']))
#    print(socket.gethostbyaddr("127.0.0.1"))
#    return socket.gethostbyaddr(request.META['REMOTE_ADDR']) == socket.gethostbyaddr("127.0.0.1")
def get_cart(request:HttpRequest):
    session_id = request.session.session_key
    return Cart.objects.get(customer = request.user.customer) if request.user.is_authenticated else Cart.objects.get(session_id=session_id)
@require_http_methods(['POST'])
def add(request:HttpRequest):
    item_id = request.POST.get('item_id', None)
    item_amount = int(request.POST.get('quantity', "1"))
    try:
        CartManager.add(request, item_id, item_amount)
    except CartManager.QuantityError as qe:
        return HttpResponse(str(qe), status = 400)
    except Ware.DoesNotExist:
        return HttpResponseBadRequest("Invalid ware id provided")
    return HttpResponse(status=200)


@require_http_methods(['POST'])
def remove(request:HttpRequest):
    item_id = request.POST.get('item_id', None)
    item_amount = int(request.POST.get('item_amount', "1"))
    try:
        CartManager.remove(item_id, item_amount)
    except CartWare.DoesNotExist:
        return HttpResponse("The ware is not in cart", status = 202)
    except CartManager.QuantityError as qe:
        return HttpResponse(str(qe), status = 400)
    return HttpResponse(status=200)