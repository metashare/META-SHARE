from django.contrib.auth.models import User, Group
from django_selenium.testcases import SeleniumTestCase
from metashare import settings, test_utils
from metashare.repository.models import resourceInfoType_model
from metashare.repository.seltests.test_utils import login_user, mouse_over, \
    setup_screenshots_folder
from metashare.settings import DJANGO_BASE, ROOT_PATH
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import time


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
        
        # load test fixture and set its status to 'published'
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
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_corpus_text")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "editoruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a[3]/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Editor
        driver.find_element_by_css_selector("div.button.middle_button").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Share/Create Resource
        mouse_over(driver, driver.find_element_by_link_text("Share/Create"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_link_text("Resource").click()
        # create text corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusTextInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
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
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup       
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        self.fill_contact_person(driver, ss_path, root_id)
        
        # corpus info text popup
        driver.find_element_by_id("add_id_corpusTextInfo-0").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        ###Select(driver.find_element_by_id("id_mediaType")).select_by_visible_text("text")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "monolingual")
        # corpus info text / language popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        driver.switch_to_window("id_languageInfo")
        driver.find_element_by_id("id_languageId").clear()
        driver.find_element_by_id("id_languageId").send_keys("De")
        driver.find_element_by_id("id_languageName").clear()
        driver.find_element_by_id("id_languageName").send_keys("German")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        # corpus info text / size popup
        driver.find_element_by_css_selector("#add_id_sizeInfo > img[alt=\"Add Another\"]").click()
        driver.switch_to_window("id_sizeInfo")
        driver.find_element_by_id("id_size").clear()
        driver.find_element_by_id("id_size").send_keys("10000")
        Select(driver.find_element_by_id("id_sizeUnit")).select_by_visible_text("tokens")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        # save and close corpus info text popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)
        
        # save text corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Text Corpus\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)
          
        
    def test_LR_creation_lang_descr_text(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_lang_descr_text")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "editoruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a[3]/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Editor
        driver.find_element_by_css_selector("div.button.middle_button").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Share/Create Resource
        mouse_over(driver, driver.find_element_by_link_text("Share/Create"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_link_text("Resource").click()
        # create language description
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Language description")
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle
        # add required fields
        driver.find_element_by_id("id_form-0-resourceName").clear()
        driver.find_element_by_id("id_form-0-resourceName").send_keys("Test Text Language Description")
        driver.find_element_by_id("id_form-0-description").clear()
        driver.find_element_by_id("id_form-0-description").send_keys("Test Description")
        driver.find_element_by_link_text("Today").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup       
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        self.fill_contact_person(driver, ss_path, root_id)
        
        # language description general info popup
        driver.find_element_by_id("edit_id_langdescInfo").click()
        driver.switch_to_window("edit_id_langdescInfo")
        Select(driver.find_element_by_id("id_languageDescriptionType")).select_by_visible_text(
          "grammar")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)
          
        # language description info text popup
        driver.find_element_by_id("add_id_languageDescriptionTextInfo").click()
        driver.switch_to_window("id_languageDescriptionTextInfo")
        ###Select(driver.find_element_by_id("id_mediaType")).select_by_visible_text("text")
        Select(driver.find_element_by_id("id_form-2-0-lingualityType")).select_by_visible_text(
          "monolingual")
        # language description info text / language popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        driver.switch_to_window("id_languageInfo")
        driver.find_element_by_id("id_languageId").clear()
        driver.find_element_by_id("id_languageId").send_keys("De")
        driver.find_element_by_id("id_languageName").clear()
        driver.find_element_by_id("id_languageName").send_keys("German")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window("id_languageDescriptionTextInfo")
        # save and close language description info text popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)

        # save language description text
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Text Language Description\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)
        
        
    def fill_distribution(self, driver, ss_path, root_id):
        """
        fills the distribution popup with required information and returns
        to the original window
        """
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        driver.switch_to_window("id_distributionInfo")
        Select(driver.find_element_by_id("id_availability")).select_by_visible_text("available-unrestrictedUse")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)
        
        
    def fill_contact_person(self, driver, ss_path, root_id):
        """
        fills the contact person popup with required information and returns
        to the original window
        """
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        driver.switch_to_window("id_contactPerson")
        driver.find_element_by_id("id_surname").clear()
        driver.find_element_by_id("id_surname").send_keys("Mustermann")
        driver.find_element_by_id("id_form-0-email").clear()
        driver.find_element_by_id("id_form-0-email").send_keys("mustermann@org.com")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)
        
        
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
