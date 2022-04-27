from django.db.models import Manager, QuerySet
from django.http import HttpRequest
from django.db.models import QuerySet, F
from django.core.cache import cache
import logging
from django.contrib.auth.password_validation import validate_password
from django.db.transaction import atomic
from datetime import datetime, timedelta, timezone
from cms_site.utils.mailing import send_email_confirmation, send_password_reset
from cms_site.utils.tokens import gen_uuid4_hex
import cms_site.models as models
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import UserManager as ContribUserManager, Group
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
log = logging.getLogger(__name__)
class CartManager:
    @staticmethod
    def resolve_cart(request:HttpRequest):
        if hasattr(request, 'data') and 'cart' in request.data: return request.data['cart']
        if request.user.is_authenticated:
            #try get cart by sessionid
            cart = models.Cart.objects.filter(session_id = request.session.session_key).select_related('customer').first()
            if cart:
                # case where user got cart before sign up
                # if cart has no customer, but they exist, set customer to that cart
                if not cart.customer:
                    cart.customer = request.user.customer
                    cart.save()
                    log.info(f'Customer {cart.customer.id} has been assigned to cart {cart.id}')
                else:
                    if cart.customer != request.user.customer:
                        log.critical(f"!!! CART WAS ASSIGNED TO A WRONG CUSTOMER, THIS SHOULD NEVER HAPPEN. OWNER {cart.customer.id}, REQUEST USER {request.user.customer.id} ")
            # couldn't find cart by session id
            # get or create cart by customer
            else:
                log.info(f'Couldn\'t find cart by session id. Getting from customer or creating new...')
                cart, created = models.Cart.objects.select_related('customer').get_or_create(
                    customer = request.user.customer,
                    defaults={'customer': request.user.customer, 'session_id':request.session.session_key},
                )
                # session of customer was found, update session_id
                if not created:
                    cart.session_id = request.session.session_key
                log.info(f'Cart {cart.id} resolved for authenticated customer {request.user.customer.id}. Was created: {created}')
        else:
            cart, created = models.Cart.objects.select_related('customer').get_or_create(
                session_id = request.session.session_key,
                defaults={'session_id': request.session.session_key},
            )
            log.info(f'Cart {cart.id} resolved for unauthenticated user. Was created: {created}')
        return cart
    @staticmethod
    def remove(request:HttpRequest, item_id, item_amount):
        if not item_amount or item_amount < 0: 
            raise CartManager.QuantityError('Invalid item_amount')
        if not item_id:
            raise models.CartWare.DoesNotExist('Invalid item id provided')
        cart = CartManager.resolve_cart(request)
        with atomic():
            cart_ware = models.CartWare.objects.only('quantity').get(cart=cart, ware__id=item_id)
            cart_ware.quantity -= item_amount
            if cart_ware.quantity<=0:
                cart_ware.delete()
                return None
            cart_ware.save()
            return cart_ware
    @staticmethod
    def add(request:HttpRequest, item_id, item_amount):
        if not item_amount or item_amount < 0: 
            raise CartManager.QuantityError('Invalid item_amount')
        if not item_id:
            raise models.Ware.DoesNotExist('Invalid item id provided')
        with atomic():
            cart = CartManager.resolve_cart(request)
            cart_ware = models.CartWare.objects.filter(cart=cart, ware__id=item_id). \
            select_related('ware').\
            only('quantity','ware__quantity').\
            first()
            if cart_ware:
                if(cart_ware.ware.quantity < item_amount):
                    raise CartManager.QuantityError(f"Not enough wares in stock. Wares available: {cart_ware.ware.quantity}")
                cart_ware.quantity += item_amount
                cart_ware.save()
            else:   
                ware = models.Ware.objects.only('quantity').get(id=item_id)
                if(ware.quantity < item_amount):
                    raise CartManager.QuantityError(f"Not enough wares in stock. Wares available: {ware.quantity}")
                cart_ware = models.CartWare.objects.create(cart=cart, ware=ware, quantity=item_amount)
            return cart_ware

    class QuantityError(Exception):
        pass

class CacheManager:
    is_cache_populated = False

    @staticmethod
    def get_categories() -> dict:
        if not CacheManager.is_cache_populated:
             CacheManager.__populate_cache()
        return cache.get('categories',{})
    @staticmethod
    def update_categories(upd_categories):
        if not CacheManager.is_cache_populated:
             CacheManager.__populate_cache()
        categories:dict = cache.get('categories', {})
        categories.update(upd_categories)
        cache.set('categories', categories, timeout=None)
    
    @staticmethod
    def get_filters() -> dict:
        if not CacheManager.is_cache_populated:
             CacheManager.__populate_cache()
        return cache.get('filters',{})
    @staticmethod
    def update_filters(upd_filters):
        if not CacheManager.is_cache_populated:
             CacheManager.__populate_cache()
        filters:dict = cache.get('filters', {})
        filters.update(upd_filters)
        cache.set('categories', filters, timeout=None) 

    @staticmethod
    def __populate_cache():
        filters = models.Filter.objects.all()
        categories = models.Category.objects.all()
        filters = {f.name: f for f in filters}
        categories = {c.name: c for c in categories}
        cache.set('filters', filters, timeout=None)
        cache.set('categories', categories, timeout=None)
        CacheManager.is_cache_populated = True
        #log.debug('Cache populated')



class WareManager(Manager):
    
    ENTITIES_PER_REQUEST = 15
    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)
    #    self.annotate(size=F('width')+F('height'))
    def get_queryset(self):
        return WareManager.WareQuerySet(self.model, using=self._db).annotate(size=F('width')+F('height'))
        #return super().get_queryset().annotate(size=F('width')+F('height'))
    def apply_filters(self, filters):
        if filters and len(filters)>0:
            self.get_queryset().order_by(*filters)
        return self
    def apply_categories(self, categories):
        return self.get_queryset().apply_categories(categories)
    def apply_page(self, page):
        return self.get_queryset().apply_page(page)
    class WareQuerySet(QuerySet):
        def apply_categories(self, categories):
            if categories and len(categories)>0:
               return self.filter(categories__parameter__in=categories)
            return self
        def apply_page(self, page):
            i_from, i_to = WareManager.ENTITIES_PER_REQUEST * page - WareManager.ENTITIES_PER_REQUEST, WareManager.ENTITIES_PER_REQUEST*page
            return self[i_from:i_to]

class UserManager(ContribUserManager):
    def create_user(self, email, password):
        validate_password(password)
        #create temporary model for validation by full_clean()
        tmp_user = models.User()
        tmp_user.email = email
        tmp_user.username = email
        tmp_user.password = password
        tmp_user.full_clean()

        user = super().create_user(email, email, password)
        return user

class AuthManager():
    EMAIL_VERIFICATION_HOURS = 24
    PASSWORD_RESET_HOURS = 24
    @staticmethod
    def set_email_verification(user, url, email_change=None, send_email=True):
        vrf_token = gen_uuid4_hex()
        #chance of dublicate is very small, but check to make sure
        while models.User.objects.filter(email_vrf_token=vrf_token).exists():
            vrf_token = gen_uuid4_hex()
        if email_change:
            if models.User.objects.filter(email=email_change).exists():
                raise IntegrityError(f"User with {email_change} already exists")
        
        user.email_vrf_token= vrf_token
        user.email_vrf_expiration = datetime.now(timezone.utc) + timedelta(hours=AuthManager.EMAIL_VERIFICATION_HOURS)
        user.email_change = email_change
        user.full_clean()
        if send_email:
            send_email_confirmation(user.email if not email_change else email_change, f'{url}?vrft={vrf_token}')
        user.save()
        return vrf_token
    @staticmethod
    def verify_email(token):
        if not token:
            raise models.User.DoesNotExist('Invalid verification token')
        
        user = models.User.objects.\
        only('email_vrf_token', 'email_vrf_expiration', 'email_change', 'email').\
        get(email_vrf_token=token)
        
        if datetime.now(timezone.utc) > user.email_vrf_expiration:
            AuthManager.clear_email_verification(user)
            user.save()
            raise AuthManager.EmailVerificationException('Verification token expired')
        verified_group = Group.objects.get(name='verified')
        if(user.email_change):
            user.email = user.email_change
        AuthManager.clear_email_verification(user)
        with atomic():
            user.save()
            user.groups.add(verified_group)
    @staticmethod        
    def clear_email_verification(user):
        user.email_vrf_token= None
        user.email_vrf_expiration = None
        user.email_change = None

    @staticmethod
    def login(request, email, password):
        user = authenticate(request, username=email, password=password)
        if not user:
            raise PermissionDenied('Please, check email/password and try again.')
        login(request, user)
        return user
    @staticmethod
    def clear_password_reset(user):
        user.password_reset_token= None
        user.password_reset_expiration = None
    @staticmethod
    def set_password_reset(email, url, send_email=True):
        user = models.User.objects.only('password_reset_token',
                                        'password_reset_expiration').get(email=email)
        reset_token = gen_uuid4_hex()
        #chance of dublicate is very small, but check to make sure
        while models.User.objects.filter(password_reset_token=reset_token).exists():
            reset_token = gen_uuid4_hex()

        user.password_reset_token= reset_token
        user.password_reset_expiration = datetime.now(timezone.utc) + timedelta(hours=AuthManager.PASSWORD_RESET_HOURS)
        if send_email:
            send_password_reset(user.email, f'{url}?vrft={reset_token}')
        user.save()
        return reset_token, user
    @staticmethod
    def password_change(reset_token, password):
        validate_password(password)
        user = models.User.objects.only('password_reset_token',
                                        'password_reset_expiration').get(password_reset_token=reset_token)
        if datetime.now(timezone.utc) > user.password_reset_expiration:
            AuthManager.clear_password_reset(user)
            user.save()
            raise AuthManager.PasswordResetTokenExpired('Password reset token expired')
        user.set_password(password)
        AuthManager.clear_password_reset(user)
        user.save()
        return user
    
            
        
    

    class EmailVerificationException(Exception):
        pass
    class PasswordResetTokenExpired(Exception):
        pass