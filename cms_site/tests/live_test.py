
from time import sleep
from cms_site.models import User
from django.test import override_settings
from cms_site.tests.core.live import LiveTestBase



@override_settings(SKIP_MAILING=True)
class LiveSignInTest(LiveTestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        #credentials for sign up test
        cls.email = cls.test_cfg['LIVE_TEST']['EXISTING_USER_EMAIL']
        cls.password = cls.test_cfg['LIVE_TEST']['EXISTING_USER_PASSWORD']
    def _fill_signin(self, email, password, delay = 0.5):
        self.selenium.find_element_by_name("email").send_keys(email)
        sleep(delay)
        self.selenium.find_element_by_name("password").send_keys(password)
        sleep(delay)

    def _test_signin_fail(self):
        #incorrect password
        self.selenium.get(self.live_server_url+'/auth/signin')
        self._fill_signin(self.email, 'wrong')
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
        #incorrect email
        self._fill_signin('wrong@admin.com', self.password)
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
    def _test_signin_success(self):
        self.selenium.get(self.live_server_url+'/auth/signin')
        self._fill_signin(self.email, self.password)
        self._click_submit()
        #check if redirected (success)
        self.assertEqual(self.selenium.current_url.rstrip('/'), self.live_server_url.rstrip('/'))

@override_settings(SKIP_MAILING=True)
class LiveSignUpTest(LiveTestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        #credentials for sign up test
        cls.new_user_email = cls.test_cfg['LIVE_TEST']['NEW_USER_EMAIL']
        cls.new_user_password = cls.test_cfg['LIVE_TEST']['NEW_USER_PASSWORD']
        cls.conf_email_url = f'{cls.server_rstripped_url}/auth/emailvrf'
        cls.change_email_url = f'{cls.server_rstripped_url}/auth/emailchangevrf'
    def _fill_signup(self, email, password, conf_password, delay = 0.5):
        self.selenium.find_element_by_name("email").send_keys(email)
        sleep(delay)
        self.selenium.find_element_by_name("password").send_keys(password)
        sleep(delay)
        self.selenium.find_element_by_name("password_confirm").send_keys(conf_password)
        sleep(delay)
    def _email_verification(self):
        user = User.objects.filter(email = self.new_user_email).values('email_vrf_token').first()
        vrft = user['email_vrf_token']
        url = f'{self.server_rstripped_url}/auth/emailvrf?vrft={vrft}'
        self.selenium.get(url)
        sleep(7) #email verification status page has 5 seconds redirect delay

    #test whether errors are raised and displayed on ui
    def _test_fail(self):
        #passwords don't match
        self.selenium.get(self.live_server_url+'/auth/signup')
        self._fill_signup(self.new_user_email, self.new_user_password, 'wrong')
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
        #incorrect password format
        self._fill_signup(self.new_user_email, '11', '11')
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
        #email already occupied
        self._fill_signup('admin@admin.com', self.new_user_password, self. new_user_password)
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
    def _test_success(self):
        self.selenium.get(self.live_server_url+'/auth/signup')
        self._fill_signup(self.new_user_email, self.new_user_password, self.new_user_password)
        self._click_submit()
        #check if redirected (success)
        self.assertEqual(self.selenium_rstripped_url, self.server_rstripped_url)
        self._email_verification()
        #check if redirected (success)
        self.assertEqual(self.selenium_rstripped_url, self.server_rstripped_url)

    

@override_settings(SKIP_MAILING=True)
class LiveEmailUpdateTest(LiveSignInTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.new_user_email = cls.test_cfg['LIVE_TEST']['NEW_USER_EMAIL']
    #override with custom execution order
    def test_all(self):
        #sign in first
        self._test_signin_success()
        #email change
        self._test_change_email_fail()
        self._test_change_email_success()

    def _fill_email_change(self, email, password, delay = 0.5):
        self.selenium.find_element_by_name("new_email").send_keys(email)
        sleep(delay)
        self.selenium.find_element_by_name("password").send_keys(password)
        sleep(delay)
    def _email_verification(self):
        user = User.objects.filter(email = self.email).values('email_vrf_token').first()
        vrft = user['email_vrf_token']
        url = f'{self.server_rstripped_url}/auth/emailchangevrf?vrft={vrft}'
        self.selenium.get(url)
        sleep(7) #email verification status page has 5 seconds redirect delay
    
    def _test_change_email_success(self):
        self.selenium.get(self.live_server_url+'/auth/emailchange')
        self._fill_email_change(self.new_user_email, self.password)
        self._click_submit()
        self._email_verification()
        #check if on index page
        self.assertEqual(self.selenium_rstripped_url, self.server_rstripped_url)
    def _test_change_email_fail(self):
        self.selenium.get(self.live_server_url+'/auth/emailchange')
        #wrong password
        self._fill_email_change('new@email.com', 'wrong')
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
        #email already occupied
        self._fill_email_change('admin@admin.com', self.password)
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
    


@override_settings(SKIP_MAILING=True)
class LivePasswordUpdateTest(LiveSignInTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        #credentials for sign up test
        cls.new_user_email = cls.test_cfg['LIVE_TEST']['NEW_USER_EMAIL']
    #override with custom execution order
    def test_all(self):
        #sign in first
        self._test_signin_success()
        #password reset
        self._test_password_change_fail_1()
        self._test_password_change_success_1()
        self._test_password_change_fail_2()
        self._test_password_change_success_2()
        #django logs out user when email changes
        self._test_signin_success()
        self.assertEqual(self.selenium_rstripped_url, self.server_rstripped_url)

    def _fill_pwd_reset_1(self, email, delay = 0.5):
        self.selenium.find_element_by_name("email").send_keys(email)
        sleep(delay)
    def _fill_pwd_reset_2(self, password, password_confirm, delay = 0.5):
        self.selenium.find_element_by_name("password").send_keys(password)
        sleep(delay)
        self.selenium.find_element_by_name("password_confirm").send_keys(password_confirm)
        sleep(delay)
    
    def _test_password_change_fail_1(self):
        self.selenium.get(self.live_server_url+'/auth/pwdreset1')
        #wrong email
        self._fill_pwd_reset_1('wrong@email.com')
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
    def _test_password_change_success_1(self):
        self.selenium.get(self.live_server_url+'/auth/pwdreset1')
        #use this only AFTER email change
        #consider better test isolation
        self._fill_pwd_reset_1(self.email)
        self._click_submit()
        #check if on index page
        self.assertEqual(self.selenium_rstripped_url, self.server_rstripped_url)
    def _test_password_change_fail_2(self):
        user = User.objects.filter(email = self.email).values('password_reset_token').first()
        token = user['password_reset_token']
        url = f'{self.server_rstripped_url}/auth/pwdreset2?rst={token}'
        self.selenium.get(url)
        #passwords don't match
        self._fill_pwd_reset_2('pwd', 'wrong')
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
        #invalid password
        self._fill_pwd_reset_2('11', '11')
        self._click_submit()
        self.assertIsNotNone(self.selenium.find_element_by_id('message').text)
        sleep(0.5)
    def _test_password_change_success_2(self):
        user = User.objects.filter(email = self.email).values('password_reset_token').first()
        token = user['password_reset_token']
        url = f'{self.server_rstripped_url}/auth/pwdreset2?rst={token}'
        self.selenium.get(url)
        self._fill_pwd_reset_2('newpassword_111', 'newpassword_111')
        self._click_submit()
        #check if on signin page
        #pwdreset2->signin
        self.assertEqual(self.selenium_rstripped_url, self.server_rstripped_url+'/auth/signin')
        self.password = 'newpassword_111'

class LiveIndexTest(LiveTestBase):
    def _test_index(self):
        self.selenium.get(self.live_server_url)
        self._scrollToBottom(0.02)