from distutils.file_util import write_file
from django.http import HttpRequest, FileResponse, HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render
#import socket
#
#
#def is_localhost(request):
#    print(socket.gethostbyaddr(request.META['REMOTE_ADDR']))
#    print(socket.gethostbyaddr("127.0.0.1"))
#    return socket.gethostbyaddr(request.META['REMOTE_ADDR']) == socket.gethostbyaddr("127.0.0.1")
    

def openapi(request:HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden()
    if request.method=='POST':
        api_docs = request.POST['api_file']
        with open('openapi.json', 'w+') as file:
            file.write(api_docs)
    return render(request, 'dev/openapi.html')

def openapi_ui(request:HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden()
    with open('openapi.json', 'r') as file:
        api_docs = file.read()
    return render(request, 'dev/swg/index.html', context={'spec':api_docs})
