from datetime import datetime, timedelta, timezone
from django.test import TestCase, RequestFactory
import cms_site.managers as managers
from cms_site.settings import BASE_DIR
from os.path import join
import cms_site.models as models
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

class CacheManagerTest(TestCase):
    fixtures = [
        join(BASE_DIR, 'cms_site/tests/fixtures/test_filters.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_categories.json'),
    ]
    def test_get_filters(self):
        filters = managers.CacheManager.get_filters()
        self.assertEqual(len(filters), 2)
        self.assertIsInstance(filters['Size'], models.Filter)
    def test_get_categories(self):
        categories = managers.CacheManager.get_categories()
        self.assertEqual(len(categories), 3)
        self.assertIsInstance(categories['Medium'], models.Category)

class CartManagerTest(TestCase):
    fixtures=[
        join(BASE_DIR, 'cms_site/tests/fixtures/test_categories.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_filters.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_groups.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_wares.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_users.json'),
    ]
    def _create_request(self):
        request = self.request_factory.get('http://example.com/')
        self.session_middleware.process_request(request)
        self.auth_middleware.process_request(request)
        request.session.save()
        return request
    def setUp(self):
        self.request_factory = RequestFactory()
        self.session_middleware = SessionMiddleware()
        self.auth_middleware = AuthenticationMiddleware()

    def test_resolve_session(self):
        request= self._create_request()
        cart = managers.CartManager.resolve_cart(request)
        self.assertIsNotNone(cart)
    def test_resolve_customer(self):
        models.User.objects.create_user('test2.create@test.com', 'test2pwd')
        request= self._create_request()
        managers.AuthManager.login(request, 'test2.create@test.com', 'test2pwd')
        cart = managers.CartManager.resolve_cart(request)
        self.assertIsNotNone(cart)
    def test_add_remove(self):
        request = self._create_request()
        #quantity <= 0 or None
        self.assertRaises(managers.CartManager.QuantityError, 
            lambda: managers.CartManager.add(request, 1, 0))
        self.assertRaises(managers.CartManager.QuantityError, 
            lambda: managers.CartManager.add(request, 1, None))
        self.assertRaises(managers.CartManager.QuantityError, 
            lambda: managers.CartManager.remove(request, 1, 0))
        self.assertRaises(managers.CartManager.QuantityError, 
            lambda: managers.CartManager.remove(request, 1, None))
        #quantity > ware.quantity
        self.assertRaises(managers.CartManager.QuantityError, 
            lambda: managers.CartManager.add(request, 1, 2))
        #ware does not exist
        self.assertRaises(models.Ware.DoesNotExist, 
            lambda: managers.CartManager.add(request, 22, 1))
        self.assertRaises(models.Ware.DoesNotExist, 
            lambda: managers.CartManager.add(request, None, 1))
        self.assertRaises(models.CartWare.DoesNotExist, 
            lambda: managers.CartManager.remove(request, 22, 1))
        self.assertRaises(models.CartWare.DoesNotExist, 
            lambda: managers.CartManager.remove(request, None, 1))
        #success add
        #new
        cart_ware = managers.CartManager.add(request, 2, 2)
        self.assertIsNotNone(cart_ware)
        #increment
        cart_ware = managers.CartManager.add(request, 2, 2)
        self.assertEqual(cart_ware.quantity, 4)
        #success remove
        #decrement
        cart_ware = managers.CartManager.remove(request, 2, 2)
        self.assertEqual(cart_ware.quantity, 2)
        cart_ware = managers.CartManager.remove(request, 2, 2)
        self.assertIsNone(cart_ware)

class AuthManagerTest(TestCase):
    fixtures=[
        join(BASE_DIR, 'cms_site/tests/fixtures/test_users.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_groups.json')
        ]
    def setUp(self):
        self.request_factory = RequestFactory()
        self.session_middleware = SessionMiddleware()
    def test_email_verification(self):
        user:models.User = models.User.objects.create_user('test2.create@test.com', 'test2pwd')
        vrf_token = managers.AuthManager.set_email_verification(user, 'http://example.com/', email_change='new@example.com', send_email=False)
        self.assertGreaterEqual(len(user.email_vrf_token), 6)
        self.assertEqual(user.email_change, 'new@example.com')
        #wrong token
        self.assertRaises(models.User.DoesNotExist, lambda: managers.AuthManager.verify_email("24125215215"))
        #expired token
        user.email_vrf_expiration = datetime.now(timezone.utc)-timedelta(hours=2)
        user.save()
        self.assertRaises(managers.AuthManager.EmailVerificationException, lambda: managers.AuthManager.verify_email(vrf_token))
        #success
        user.email_vrf_expiration = datetime.now(timezone.utc)+timedelta(hours=2)
        user.save()
        managers.AuthManager.verify_email(vrf_token)
        #clean up
        user = models.User.objects.get(email='new@example.com')
        self.assertIsNone(user.email_vrf_token)
        self.assertIsNone(user.email_vrf_expiration)
        self.assertIsNone(user.email_change)
        self.assertTrue(user.is_verified)
        
    def test_password_reset(self):
        user:models.User = models.User.objects.create_user('test3.create@test.com', 'test3pwd')
        prev_hash = user.password #old password
        reset_token, user = managers.AuthManager.set_password_reset('test3.create@test.com', 'http://example.com/', send_email=False)
        self.assertGreaterEqual(len(user.password_reset_token), 6)
        self.assertIsNotNone(user.password_reset_expiration)
        #invalid password
        self.assertRaises(ValidationError, lambda: managers.AuthManager.password_change(reset_token, '11'))
        #token expired
        user.password_reset_expiration = datetime.now(timezone.utc)-timedelta(hours=2)
        user.save()
        self.assertRaises(managers.AuthManager.PasswordResetTokenExpired, lambda: managers.AuthManager.password_change(reset_token, 'newpassword111'))
        user.password_reset_expiration = datetime.now(timezone.utc)+timedelta(hours=2)
        user.save()
        #success
        user = managers.AuthManager.password_change(reset_token, 'newpassword111')
        #clean up
        self.assertIsNone(user.password_reset_token)
        self.assertIsNone(user.password_reset_expiration)
        self.assertNotEqual(prev_hash, user.password) #password changed
    def test_login(self):
        request = self.request_factory.post('http://example.com/auth/login')
        self.session_middleware.process_request(request)
        user:models.User = models.User.objects.create_user('test4.create@test.com', 'test4pwd')
        user = managers.AuthManager.login(request, 'test4.create@test.com', 'test4pwd')
        self.assertIsNotNone(user)
    def test_login_failed(self):
        request = self.request_factory.post('http://example.com/auth/login')
        self.session_middleware.process_request(request)
        user:models.User = models.User.objects.create_user('test5.create@test.com', 'test5pwd')
        login_lambda = lambda: managers.AuthManager.login(request, user.email, 'TT')
        self.assertRaises(PermissionDenied, login_lambda)

class UserManagerTest(TestCase):
    fixtures=[
        join(BASE_DIR, 'cms_site/tests/fixtures/test_groups.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_users.json')
        ]
    def test_create_user(self):
        user = models.User.objects.create_user('test1.create@test.com', 'test1pwd')
        self.assertIsNotNone(user)
    def test_create_user_bad_email(self):
        self.assertRaises(ValidationError, lambda: models.User.objects.create_user('test1.create*test.com', 'test1pwd'))
    def test_create_user_bad_password(self):
        self.assertRaises(ValidationError, lambda: models.User.objects.create_user('test1.create@test.com', ''))

class WareManagerTest(TestCase):
    fixtures = [
        join(BASE_DIR, 'cms_site/tests/fixtures/test_filters.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_categories.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_wares.json'),
    ]
    def test_order_categories_page(self):
        wares = list(models.Ware.objects.apply_categories(['medium']).order_by(*['-size']).apply_page(1))
        self.assertEqual(len(wares), 4)
        self.assertEqual(wares[0].id, 2)
        self.assertEqual(wares[-1].id, 7)

