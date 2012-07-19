from django.contrib.auth.models import User
from django_selenium.testcases import SeleniumTestCase
from metashare import test_utils
from metashare.repository.models import resourceInfoType_model
from metashare.settings import ROOT_PATH, DJANGO_BASE
from selenium.common.exceptions import NoSuchElementException

class ExampleSeleniumTest(SeleniumTestCase):

    def setUp(self):
        
        test_utils.setup_test_storage()
        _fixture = '{0}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        self.resource_id = _result[0].id
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.published = True
        resource.storage_object.save()
        # set up test users with and without staff permissions.
        # These will live in the test database only, so will not
        # pollute the "normal" development db or the production db.
        # As a consequence, they need no valuable password.
        staffuser = User.objects.create_user('staffuser', 'staff@example.com',
          'secret')
        staffuser.is_staff = True
        staffuser.save()
        User.objects.create_user('normaluser', 'normal@example.com', 'secret')

        super(ExampleSeleniumTest, self).setUp()
        self.base_url = 'http://{}:{}/{}' \
            .format(self.testserver_host, self.testserver_port, DJANGO_BASE)

    def test_login_logout(self):
        driver = self.driver
        # check start site
        driver.get(self.base_url)
        self.assertEqual("META-SHARE", driver.title)
        self.assertEqual("1 language resources at your disposal...", 
          driver.find_element_by_xpath(
            "//div[@id='content']/div[3]/div/p[2]").text)
        # login normaluser
        # TODO remove this workaround when Selenium starts working again as intended
        driver.set_window_size(1280, 1024)
        driver.find_element_by_xpath(
          "//div[@id='inner']/div[2]/a[2]/div").click()
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("normaluser")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("secret")
        driver.find_element_by_css_selector(
          "input.button.middle_button").click()
        self.assertEqual(
          "Username: normaluser", 
          driver.find_element_by_css_selector("p > i").text)
        # click 'browse'
        driver.find_element_by_id("browse").click()
        self.assertEqual(
          "Search", driver.find_element_by_css_selector("input#search_button").get_attribute("value"))
        # logout normaluser
        driver.find_element_by_xpath(
          "//div[@id='inner']/div[2]/a[2]/div").click()
        self.assertEqual(
          "Login", 
          driver.find_element_by_xpath(
            "//div[@id='inner']/div[2]/a[2]/div").text)
    
    def is_element_present(self, how, what):
        try: 
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException: 
            return False
        return True
    
    def tearDown(self):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()

        super(ExampleSeleniumTest, self).tearDown()
