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
from django.core.management import call_command


TESTFIXTURE_XML = '{}/repository/fixtures/ILSP10.xml'.format(ROOT_PATH)

class EditorTest(SeleniumTestCase):
    
    
    def setUp(self):
        # create editor user
        editoruser = User.objects.create_user(
          'editoruser', 'editor@example.com', 'secret')
        editoruser.is_staff = True
        globaleditors = Group.objects.get(name='globaleditors')
        editoruser.groups.add(globaleditors)
        editoruser.save()
        # make sure the index does not contain any stale entries
        call_command('rebuild_index', interactive=False, using=settings.TEST_MODE_NAME)
        
        # init Selenium
        driver = getattr(webdriver, settings.SELENIUM_DRIVER, None)
        assert driver, "settings.SELENIUM_DRIVER contains non-existing driver"
        self.driver = driver()
        self.driver.implicitly_wait(30)
        host = getattr(settings, 'SELENIUM_TESTSERVER_HOST', 'localhost')
        port = getattr(settings, 'SELENIUM_TESTSERVER_PORT', 8000)
        self.base_url = 'http://{0}:{1}/{2}'.format(host, port, DJANGO_BASE)
        self.verification_errors = []

    
    def tearDown(self):
        resourceInfoType_model.objects.all().delete()
        User.objects.all().delete()
        
        # clean up Selenium
        self.driver.quit()
        self.assertEqual([], self.verification_errors)


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
        # go to Update->Resource
        mouse_over(driver, driver.find_element_by_link_text("Update"))
        driver.find_element_by_link_text("Resource").click()        # make sure we are on the right site
        self.assertEqual("Select Resource to change | META-SHARE backend", driver.title)
        # check if LR entry is available and that its status is published
        try: 
            self.assertEqual("REVEAL-THIS Corpus",
                driver.find_element_by_link_text("REVEAL-THIS Corpus").text)
        except AssertionError as e: 
            self.verification_errors.append(str(e))
        try: 
            self.assertEqual(
              "published", 
              driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr/td[3]").text)
        except AssertionError as e: 
            self.verification_errors.append(str(e))
        # click LR to edit it
        driver.find_element_by_link_text("REVEAL-THIS Corpus").click()
        # change the short name and save the LR
        driver.find_element_by_name("key_form-0-resourceShortName_0").clear()
        driver.find_element_by_name("key_form-0-resourceShortName_0").send_keys("en")
        driver.find_element_by_name("val_form-0-resourceShortName_0").clear()
        driver.find_element_by_name("val_form-0-resourceShortName_0").send_keys("a random short name")
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
        driver.find_element_by_name("key_form-0-resourceName_0").clear()
        driver.find_element_by_name("key_form-0-resourceName_0").send_keys("en")
        driver.find_element_by_name("val_form-0-resourceName_0").clear()
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Text Corpus")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.find_element_by_link_text("Today").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
        # corpus info text popup
        driver.find_element_by_id("add_id_corpusTextInfo-0").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "monolingual")
        # corpus info text / language popup
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # corpus info text / size popup
        self.fill_size(driver, ss_path, "sizeinfotype_model_set-0-")
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
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(
          "Language description")
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle
        # add required fields
        driver.find_element_by_name("key_form-0-resourceName_0").clear()
        driver.find_element_by_name("key_form-0-resourceName_0").send_keys("en")
        driver.find_element_by_name("val_form-0-resourceName_0").clear()
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Text Language Description")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.find_element_by_link_text("Today").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
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
        Select(driver.find_element_by_id("id_form-2-0-lingualityType")).select_by_visible_text(
          "monolingual")
        # language description info text / language popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
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
        

    def test_LR_creation_lex_resource_text(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_lex_resource_text")
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
        # create lexical resource
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(
          "Lexical conceptual resource")
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle
        # add required fields
        driver.find_element_by_name("key_form-0-resourceName_0").clear()
        driver.find_element_by_name("key_form-0-resourceName_0").send_keys("en")
        driver.find_element_by_name("val_form-0-resourceName_0").clear()
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Lexical Resource Text")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.find_element_by_link_text("Today").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
        # lexical resource general info popup
        driver.find_element_by_id("edit_id_lexiconInfo").click()
        driver.switch_to_window("edit_id_lexiconInfo")
        Select(driver.find_element_by_id("id_lexicalConceptualResourceType")).select_by_visible_text(
          "wordList")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)
          
        # lexical resource text info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceTextInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceTextInfo")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "monolingual")
        # lexical resource text info / language popup
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # lexical resource text info / size popup
        self.fill_size(driver, ss_path, "sizeinfotype_model_set-0-")
        # save and close lexical resource text info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)

        # save lexical resource text
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Lexical Resource Text\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)
        
        
    def test_LR_creation_tool(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_tool")
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
        # create tool
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(
          "Tool / Service")
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle
        # add required fields
        driver.find_element_by_name("key_form-0-resourceName_0").clear()
        driver.find_element_by_name("key_form-0-resourceName_0").send_keys("en")
        driver.find_element_by_name("val_form-0-resourceName_0").clear()
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Tool")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.find_element_by_link_text("Today").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
        # tool info popup
        driver.find_element_by_id("edit_id_toolServiceInfo").click()
        driver.switch_to_window("edit_id_toolServiceInfo")
        Select(driver.find_element_by_id("id_toolServiceType")).select_by_visible_text("tool")
        Select(driver.find_element_by_id("id_languageDependent")).select_by_visible_text("Yes")
        # save and close tool info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)

        # save tool
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Tool\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)
        

    def test_sorting(self):
        """
        tests the sorting of controlled vocabulary in some examplary CharFields
        used in the Editor
        """
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
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        driver.switch_to_window("id_distributionInfo")
        # check sorting of Availability
        self.assertEqual("available-restrictedUse", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[2]").text)
        self.assertEqual("available-unrestrictedUse", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[3]").text)
        self.assertEqual("notAvailableThroughMetaShare", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[4]").text)        
        self.assertEqual("underNegotiation", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[5]").text)
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(root_id)
        # corpus info text popup
        driver.find_element_by_id("add_id_corpusTextInfo-0").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        # check sorting of Linguality
        self.assertEqual("bilingual", driver.find_element_by_xpath(
          "//select[@id='id_form-0-lingualityType']/option[2]").text)
        self.assertEqual("monolingual", driver.find_element_by_xpath(
          "//select[@id='id_form-0-lingualityType']/option[3]").text)
        self.assertEqual("multilingual", driver.find_element_by_xpath(
          "//select[@id='id_form-0-lingualityType']/option[4]").text)
        # check sorting of Size unit
        self.assertEqual("4-grams", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[2]").text)
        self.assertEqual("5-grams", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[3]").text)
        self.assertEqual("articles", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[4]").text)
        self.assertEqual("bigrams", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[5]").text)
        self.assertEqual("bytes", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[6]").text)
        self.assertEqual("classes", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[7]").text)
        self.assertEqual("concepts", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[8]").text)                                        
        self.assertEqual("diphones", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[9]").text)
        self.assertEqual("elements", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[10]").text)    
        # skip to end of list 
        self.assertEqual("words", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[50]").text)        

        
    def fill_distribution(self, driver, ss_path, parent_id):
        """
        fills the distribution popup with required information and returns
        to the parent window
        """
        driver.switch_to_window("id_distributionInfo")
        Select(driver.find_element_by_id("id_availability")).select_by_visible_text(
          "available-unrestrictedUse")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(parent_id)
        
        
    def fill_contact_person(self, driver, ss_path, parent_id):
        """
        fills the contact person popup with required information and returns
        to the parent window
        """
        driver.switch_to_window("id_contactPerson")
        driver.find_element_by_name("key_surname_0").clear()
        driver.find_element_by_name("key_surname_0").send_keys("en")
        driver.find_element_by_name("val_surname_0").clear()
        driver.find_element_by_name("val_surname_0").send_keys("Mustermann")
        driver.find_element_by_id("id_form-0-email").clear()
        driver.find_element_by_id("id_form-0-email").send_keys("mustermann@org.com")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        driver.switch_to_window(parent_id)
        
        
    def fill_language(self, driver, ss_path, id_infix):
        """
        fills the language popup with required information and returns to the
        parent window
        """
        driver.find_element_by_id("id_{}languageId".format(id_infix)).clear()
        driver.find_element_by_id("id_{}languageId".format(id_infix)).send_keys("De")
        driver.find_element_by_id("id_{}languageName".format(id_infix)).clear()
        driver.find_element_by_id("id_{}languageName".format(id_infix)).send_keys("German")
        
        
    def fill_size(self, driver, ss_path, id_infix):
        """
        fills the size popup with required information and returns to the
        parent window
        """
        driver.find_element_by_id("id_{}size".format(id_infix)).clear()
        driver.find_element_by_id("id_{}size".format(id_infix)).send_keys("10000")
        Select(driver.find_element_by_id("id_{}sizeUnit".format(id_infix))).select_by_visible_text("tokens")

        
    def is_element_present(self, how, what):
        try: 
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

