from django.contrib.auth.models import User, Group
from django_selenium.testcases import SeleniumTestCase
from metashare import settings, test_utils
from metashare.repository.models import resourceInfoType_model
from metashare.settings import DJANGO_BASE, ROOT_PATH
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

ADMINROOT = '/{0}editor/'.format(DJANGO_BASE)
TESTFIXTURE_XML = '{}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)

class EditorTest(SeleniumTestCase):
    
    def setUp(self):
        # init Selenium
        driver = getattr(webdriver, settings.SELENIUM_DRIVER, None)
        assert driver, "settings.SELENIUM_DRIVER contains non-existing driver"
        self.driver = driver()
        self.driver.implicitly_wait(30)
        host = getattr(settings, 'SELENIUM_TESTSERVER_HOST', 'localhost')
        port = getattr(settings, 'SELENIUM_TESTSERVER_PORT', 8000)
        self.base_url = 'http://{0}:{1}/{2}'.format(host, port, DJANGO_BASE)
        self.verificationErrors = []
        
        # load test fixure and set its status to 'published'
        test_utils.setup_test_storage()
        _result = test_utils.import_xml(TESTFIXTURE_XML)
        self.resource_id = _result[0].id
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.published = True
        resource.storage_object.save()
        
        # create editor user
        editoruser = User.objects.create_user(
          'editoruser', 'editor@example.com', 'secret')
        editoruser.is_staff = True
        globaleditors = Group.objects.get(name='globaleditors')
        editoruser.groups.add(globaleditors)
        editoruser.save()
    
    def test_status_after_saving(self):
        driver = self.driver
        driver.get(self.base_url)
        # login user
        driver.find_element_by_xpath("//div[@id='inner']/div[2]/a[2]/div").click()
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("editoruser")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("secret")
        driver.find_element_by_css_selector("input.button.middle_button").click()
        # go to Editor
        driver.find_element_by_css_selector("div.button.middle_button").click()
        # go to Update
        driver.find_element_by_link_text("Update").click()
        # make sure we are on the right site
        self.assertEqual("Select Resource to change | META-SHARE backend", driver.title)
        # check if LR entry is available and that its status is published
        try: self.assertEqual(
          "Italian TTS Speech Corpus (Appen)", 
          driver.find_element_by_link_text("Italian TTS Speech Corpus (Appen)").text)
        except AssertionError as e: 
            self.verificationErrors.append(str(e))
        try: self.assertEqual(
          "published", 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr/td[3]").text)
        except AssertionError as e: 
            self.verificationErrors.append(str(e))
        # click LR to edit it
        driver.find_element_by_link_text("Italian TTS Speech Corpus (Appen)").click()
        # add a short name and save the LR
        driver.find_element_by_id("id_form-0-resourceShortName").clear()
        driver.find_element_by_id("id_form-0-resourceShortName").send_keys("a random short name")
        driver.find_element_by_name("_save").click()
        # make sure that the LR status is still published after saving
        try: self.assertEqual(
          "published", 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr/td[3]").text)
        except AssertionError as e: 
            self.verificationErrors.append(str(e))
        
    def is_element_present(self, how, what):
        try: 
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True
    
    def tearDown(self):
        resourceInfoType_model.objects.all().delete()
        
        # clean up Selenium
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)
