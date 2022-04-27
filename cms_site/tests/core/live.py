from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from configparser import ConfigParser
from os.path import join
from cms_site.settings import BASE_DIR
from selenium.webdriver.chrome.webdriver import WebDriver
from time import sleep

class LiveTestBase(StaticLiveServerTestCase):
    """
    Base class for live testing with Selenium.
    Optimized by removing db clean up after each test.
    """
    SELENIUM_WAIT_SECONDS = 1
    fixtures = [
        join(BASE_DIR, 'cms_site/tests/fixtures/test_groups.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_users.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_customers.json'),
        join(BASE_DIR, 'cms_site/cms_setup.json'), #contains init logic for cms pages, plugins, etc. Heavy.
        join(BASE_DIR, 'cms_site/tests/fixtures/test_filters.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_categories.json'),
        join(BASE_DIR, 'cms_site/tests/fixtures/test_wares.json')
    ]
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        #conf init
        cls.test_cfg = ConfigParser()
        cls.test_cfg.read(join(BASE_DIR,'cms_site/tests/test_conf.ini'))
        #selenium init
        cls.selenium = WebDriver(cls.test_cfg['LIVE_TEST']['CHROMEDRIVER_PATH'], service_log_path=None)
        print(f'Preparing {cls.__name__}')
    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()
    #speed up testing by removing TRUNCATE between tests 
    def test_all(self):
        import inspect
        predicate = lambda value: inspect.ismethod(value) and value.__name__.startswith('_test')
        methods = inspect.getmembers(self, predicate)
        for m in methods:
            print('Running', m[0])
            m[1]()
    def _scrollToBottom(self, speed):
        for i in range(100):
            self.selenium.execute_script(f"window.scrollTo(0, document.body.scrollHeight*{i/100})")
            sleep(speed) 
    def _click_submit(self, delay = 0.5):
        self.selenium.find_element_by_id('submit').click()
        sleep(delay)
    # strip / at the end
    @property
    def selenium_rstripped_url(self):
        return self.selenium.current_url.rstrip('/')
    @property
    def server_rstripped_url(self):
        return self.live_server_url.rstrip('/')