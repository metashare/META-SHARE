from django.contrib.auth.models import User, Group
from django_selenium.testcases import SeleniumTestCase
from metashare import settings, test_utils
from metashare.repository.models import resourceInfoType_model
from metashare.repository.seltests.test_utils import login_user, mouse_over
from metashare.settings import DJANGO_BASE, ROOT_PATH
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import os

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
        self.verification_errors = []
        
        # create editor user
        editoruser = User.objects.create_user(
          'editoruser', 'editor@example.com', 'secret')
        editoruser.is_staff = True
        globaleditors = Group.objects.get(name='globaleditors')
        editoruser.groups.add(globaleditors)
        editoruser.save()
    
    
    def test_status_after_saving(self):
        
        # load test fixure and set its status to 'published'
        test_utils.setup_test_storage()
        _result = test_utils.import_xml(TESTFIXTURE_XML)
        resource = resourceInfoType_model.objects.get(pk=_result[0].id)
        resource.storage_object.published = True
        resource.storage_object.save()
    
        driver = self.driver
        driver.get(self.base_url)
        # login user
        login_user(driver, "editoruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", driver.find_element_by_xpath("//div[@id='inner']/div[2]/a[3]/div").text)
        # go to Editor
        driver.find_element_by_css_selector("div.button.middle_button").click()
        # go to Update
        driver.find_element_by_link_text("Update").click()
        # make sure we are on the right site
        self.assertEqual("Select Resource to change | META-SHARE backend", driver.title)
        # check if LR entry is available and that its status is published
        try: 
            self.assertEqual(
              "Italian TTS Speech Corpus (Appen)", 
              driver.find_element_by_link_text("Italian TTS Speech Corpus (Appen)").text)
        except AssertionError as e: 
            self.verification_errors.append(str(e))
        try: 
            self.assertEqual(
              "published", 
              driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr/td[3]").text)
        except AssertionError as e: 
            self.verification_errors.append(str(e))
        # click LR to edit it
        driver.find_element_by_link_text("Italian TTS Speech Corpus (Appen)").click()
        # add a short name and save the LR
        driver.find_element_by_id("id_form-0-resourceShortName").clear()
        driver.find_element_by_id("id_form-0-resourceShortName").send_keys("a random short name")
        driver.find_element_by_name("_save").click()
        # make sure that the LR status is still published after saving
        try: 
            self.assertEqual(
              "published", 
              driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr/td[3]").text)
        except AssertionError as e: 
            self.verification_errors.append(str(e))
            
    
    def test_LR_creation_corpus_text(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = '{}/reports/PNG-metashare.repository.seltests.test_editor.EditorTest/'.format(ROOT_PATH) + \
          'LR_creation_corpus_text'.format(ROOT_PATH)
        if not os.path.exists(ss_path):
            os.makedirs(ss_path)
        driver.get_screenshot_as_file('{}/01.png'.format(ss_path))  
        # login user
        login_user(driver, "editoruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a[3]/div").text)
        driver.get_screenshot_as_file('{}/02.png'.format(ss_path))
        # Editor
        driver.find_element_by_css_selector("div.button.middle_button").click()
        driver.get_screenshot_as_file('{}/03.png'.format(ss_path))
        # Share/Create Resource
        mouse_over(driver, driver.find_element_by_link_text("Share/Create"))
        driver.get_screenshot_as_file('{}/04.png'.format(ss_path))
        driver.find_element_by_link_text("Resource").click()
        # hover does not work, link not visible, so directly call the target url:
        #driver.get(self.base_url + "editor/repository/resourceinfotype_model/add/")
        # create text corpus
        driver.get_screenshot_as_file('{}/05.png'.format(ss_path))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusTextInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{}/06.png'.format(ss_path))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle
        # add required fields
        driver.find_element_by_id("id_form-0-resourceName").clear()
        driver.find_element_by_id("id_form-0-resourceName").send_keys("Test Text Corpus")
        driver.find_element_by_id("id_form-0-description").clear()
        driver.find_element_by_id("id_form-0-description").send_keys("Test Description")
        driver.find_element_by_link_text("Today").click()
        driver.get_screenshot_as_file('{}/07.png'.format(ss_path))
        # distribution popup       
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        driver.switch_to_window("id_distributionInfo")
        Select(driver.find_element_by_id("id_availability")).select_by_visible_text(
          "available-unrestrictedUse")
        driver.get_screenshot_as_file('{}/08.png'.format(ss_path))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        driver.switch_to_window("id_contactPerson")
        driver.find_element_by_id("id_surname").clear()
        driver.find_element_by_id("id_surname").send_keys("Mustermann")
        driver.find_element_by_id("id_form-0-email").clear()
        driver.find_element_by_id("id_form-0-email").send_keys("mustermann@org.com")
        driver.get_screenshot_as_file('{}/09.png'.format(ss_path))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)
        # corpus info text popup
        driver.find_element_by_id("add_id_corpusTextInfo-0").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        Select(driver.find_element_by_id("id_mediaType")).select_by_visible_text("text")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "monolingual")
        # corpus info text / language popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        driver.switch_to_window("id_languageInfo")
        driver.find_element_by_id("id_languageId").clear()
        driver.find_element_by_id("id_languageId").send_keys("De")
        driver.find_element_by_id("id_languageName").clear()
        driver.find_element_by_id("id_languageName").send_keys("German")
        driver.get_screenshot_as_file('{}/10.png'.format(ss_path))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        # corpus info text / size popup
        driver.find_element_by_css_selector("#add_id_sizeInfo > img[alt=\"Add Another\"]").click()
        driver.switch_to_window("id_sizeInfo")
        driver.find_element_by_id("id_size").clear()
        driver.find_element_by_id("id_size").send_keys("10000")
        Select(driver.find_element_by_id("id_sizeUnit")).select_by_visible_text("tokens")
        driver.get_screenshot_as_file('{}/11.png'.format(ss_path))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        # save and close corpus info text popup
        driver.get_screenshot_as_file('{}/12.png'.format(ss_path))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)
        # save text corpus
        driver.get_screenshot_as_file('{}/13.png'.format(ss_path))
        driver.find_element_by_name("_save").click()
        driver.get_screenshot_as_file('{}/14.png'.format(ss_path))
        self.assertEqual("The Resource \"Test Text Corpus\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        
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
        self.assertEqual([], self.verification_errors)
