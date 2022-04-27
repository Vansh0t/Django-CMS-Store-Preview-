


from django.http import HttpResponse, HttpRequest, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables
from cms_site.managers import AuthManager
from cms_site.utils.endpoints import Map
from cms_site.models import User
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


class AuthMiddleware:
    urls = Map() #map of urls
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        processor = AuthMiddleware.urls.get(request.path, None)
        result = request
        status_code = None
        if processor:
            result = processor(request)
            if issubclass(type(result), HttpResponse):
                #302 and 307 redirects have functional value for browsers and must be excluded
                #403 Forbidden goes here as well
                return result
            status_code = result.data['status']['code']

        request.data['user'] = request.user
        response = self.get_response(request)

        #set just status code, do not return HttpResponse so html page from cms could still be rendered
        if status_code:
            response.status_code = status_code

        return response







def auth_failed_response(request, error, status):
    request.data.update({'status':{'message':error,'is_error':True,'code':status}})
    return request
def status_message(request, status_message,  status, is_error, redirect=False):
    request.data.update({'status':{'message':status_message,'is_error':is_error,'code':status}, 'meta':{'timeout_redirect':redirect}})
    return request
def confirm_password(pwd1, pwd2):
    if pwd1==pwd2:
        return True
    return False

@require_http_methods(['POST', 'GET'])
@sensitive_variables('password', 'email')
@AuthMiddleware.urls.map(['/auth/signin/'])
def signin(request: HttpRequest):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('/')
    if request.method == 'GET':
        return request
    password = request.POST['password']
    email = request.POST['email']
    try:
        AuthManager.login(request, email, password)
        return redirect('/')
    except PermissionDenied as e: 
        return auth_failed_response(request, str(e), 403)
    

@require_http_methods(['POST', 'GET'])
@sensitive_variables('password', 'email', 'password_confirm')
@AuthMiddleware.urls.map(['/auth/signup/'])
def signup(request: HttpRequest):
    
    if request.method == 'GET':
        return request
    password = request.POST['password']
    password_confirm = request.POST['password_confirm']
    if not confirm_password(password, password_confirm):
        return auth_failed_response(request, 'Confirmation password doesn\'t match. Fix it and try again', 400)
    email = request.POST['email']
    try:
        with transaction.atomic():
            user = User.objects.create_user(email, password)
            url = request.build_absolute_uri(AuthMiddleware.urls.get_url(email_verify))
            AuthManager.set_email_verification(user, url)
    except ValidationError as e:
        return auth_failed_response(request, str(e), 400)
    except IntegrityError as e:
        return auth_failed_response(request, "Email is already occupied", 400)
    # if an exception occures here - 500
    AuthManager.login(request, email, password)
    return redirect('/')

@require_http_methods(['GET'])
@AuthMiddleware.urls.map(['/auth/emailvrf/'])
def email_verify(request: HttpRequest):
    token = request.GET.get('vrft', None)
    try:
        AuthManager.verify_email(token)
    except User.DoesNotExist:
        return status_message(request, 'Invalid verification credentials', 400, True)
    except AuthManager.EmailVerificationException:
        return status_message(request, 'Confirmation url is expired. TODO Get another one here.', 403, True)
    return status_message(request, 'Email confirmed.', 200, False, True)

@require_http_methods(['POST', 'GET'])
@AuthMiddleware.urls.map(['/auth/emailvrfreset/'])
def email_verify_reset(request: HttpRequest):
    user = request.user
    if user.is_authenticated and not user.is_verified:
        url = request.build_absolute_uri(AuthMiddleware.urls.get_url(email_verify))
        AuthManager.set_email_verification(user, url)
        return status_message(request, 'New email verification message is sent to your email.', 200, False, True)
    else:
        return status_message(request, 'You don\'t have access to this page.', 403, True)
    

@require_http_methods(['POST', 'GET'])
@sensitive_variables('password', 'user', 'vrf_token', 'url')
@AuthMiddleware.urls.map(['/auth/emailchange/'])
def email_change(request: HttpRequest):
    if request.method == 'GET':
        return request
    if request.user.is_authenticated and request.user.is_verified:
        new_email = request.POST['new_email']
        password = request.POST['password']
        user = authenticate(username = request.user.username, password=password)
        try:
            if not user:
                return auth_failed_response(request, 'Password  is incorrect. Please, try again.', 403)
            url = request.build_absolute_uri(AuthMiddleware.urls.get_url(email_change_verify))
            AuthManager.set_email_verification(user, url, new_email)
        except ValidationError as e:
            return auth_failed_response(request, str(e), 400)
        except IntegrityError as e:
            return auth_failed_response(request, "Email already occupied.", 400)
        return redirect('/')
    else:
        return HttpResponseForbidden()

@require_http_methods(['GET'])
@sensitive_variables('password_', 'user', 'token', 'email_vrf_token')
@AuthMiddleware.urls.map(['/auth/emailchangevrf/'])
def email_change_verify(request: HttpRequest):
    token = request.GET.get('vrft', None)
    try:
        AuthManager.verify_email(token)
    except User.DoesNotExist:
        return status_message(request, 'Forbidden.', 403, True)
    except AuthManager.EmailVerificationException:
        return status_message(request, 'Confirmation url is expired.', 403, True)
    return status_message(request, 'Email confirmed.', 200, False, True)

@require_http_methods(['GET', 'POST'])
@sensitive_variables('password_', 'user', 'reset_token', 'email', 'url')
@AuthMiddleware.urls.map(['/auth/pwdreset1/'])
def password_reset1(request: HttpRequest):
    if request.method == 'GET':
        return request
    email = request.POST['email']
    try:
        url = request.build_absolute_uri(AuthMiddleware.urls.get_url(password_reset2))
        AuthManager.set_password_reset(email, url)
        return redirect('/')
    except User.DoesNotExist:
        return auth_failed_response(request, 'User with such email is not found', 404)

@require_http_methods(['GET', 'POST'])
@sensitive_variables('password', 'password_confirm', 'user', 'reset_token', 'email', 'url')
@AuthMiddleware.urls.map(['/auth/pwdreset2/'])
def password_reset2(request: HttpRequest):
    reset_token = request.GET.get('rst', None)
    if not reset_token:
        return redirect('/')
    if request.method == 'GET':
        return request
    
    password = request.POST['password']
    password_confirm = request.POST['password_confirm']
    if not confirm_password(password, password_confirm):
        return auth_failed_response(request, 'Confirmation password doesn\'t match. Fix it and try again', 400)
    try:
        AuthManager.password_change(reset_token, password)
        return redirect(request.build_absolute_uri(AuthMiddleware.urls.get_url(signin)))
    except AuthManager.PasswordResetTokenExpired:
        return auth_failed_response(request, 'Password reset link is expired', 403) 
    except ValidationError as e:
        return auth_failed_response(request, str(e), 400)
    except User.DoesNotExist:
        return HttpResponseForbidden()



