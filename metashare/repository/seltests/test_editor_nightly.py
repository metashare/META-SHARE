import time

from django.core.management import call_command
from django_selenium.testcases import SeleniumTestCase

from selenium.webdriver.support.ui import Select

from metashare import settings, test_utils
from metashare.accounts.models import EditorGroup, EditorGroupManagers
from metashare.repository.seltests.test_editor import _delete, _publish, \
    _ingest, _fill_audio_size, _fill_contact_person, _fill_distribution, \
    _fill_language, _fill_text_size
from metashare.repository.seltests.test_utils import login_user, mouse_over, \
    setup_screenshots_folder, click_menu_item, save_and_close, \
    cancel_and_close, cancel_and_continue
from metashare.settings import DJANGO_BASE


class NightlyEditorTests(SeleniumTestCase):
    """
    Metadata editor tests that take some time to run and which are therefore
    meant to be run in nightly Jenkins builds only.
    """

    def setUp(self):
        # create an editor group and a manager group for this group
        self.test_editor_group = EditorGroup.objects.create(
            name='test_editor_group')
        self.test_manager_group = EditorGroupManagers.objects.create(
            name='test_manager_group', managed_group=self.test_editor_group)
        # create an editor group managing user
        self.manager_user = test_utils.create_manager_user('manageruser',
            'manager@example.com', 'secret',
            (self.test_editor_group, self.test_manager_group))
        self.manager_user.get_profile().default_editor_groups \
            .add(self.test_editor_group)

        # make sure the index does not contain any stale entries
        call_command('rebuild_index', interactive=False, using=settings.TEST_MODE_NAME)

        super(NightlyEditorTests, self).setUp()
        self.base_url = 'http://{}:{}/{}' \
            .format(self.testserver_host, self.testserver_port, DJANGO_BASE)
        self.verification_errors = []


    def tearDown(self):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()

        super(NightlyEditorTests, self).tearDown()
        self.assertEqual([], self.verification_errors)


    def test_LR_creation_corpus_text(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_corpus_text")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
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
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # corpus text info popup
        driver.find_element_by_id("add_id_corpusTextInfo-0").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # corpus text info / language
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # corpus text info / size
        _fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
        # save and close corpus text info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)
        
        # save text corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Text Corpus\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)
        
        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        
        
    def test_LR_creation_corpus_audio(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_corpus_audio")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create audio corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusAudioInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Audio Corpus")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # corpus audio info popup
        driver.find_element_by_id("add_id_corpusAudioInfo").click()
        driver.switch_to_window("id_corpusAudioInfo")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # corpus audio info / language
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # corpus audio info / size popup
        driver.find_element_by_css_selector("#add_id_audioSizeInfo > img[alt=\"Add Another\"]").click()
        _fill_audio_size(driver, ss_path, "id_corpusAudioInfo")
        # save and close corpus audio info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)
        
        # save audio corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Audio Corpus\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)

        
    def test_LR_creation_corpus_video(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_corpus_video")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create audio corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusVideoInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Video Corpus")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # corpus video info popup
        driver.find_element_by_id("add_id_corpusVideoInfo-0").click()
        driver.switch_to_window("id_corpusVideoInfo__dash__0")
        # corpus video info / size popup
        driver.find_element_by_name("sizeinfotype_model_set-0-size").clear()
        driver.find_element_by_name("sizeinfotype_model_set-0-size").send_keys("100")
        driver.find_element_by_name("sizeinfotype_model_set-0-sizeUnit").send_keys("Gb")
        # save and close corpus video info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)
        
        # save video corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Video Corpus\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)

        
    def test_LR_creation_corpus_image(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_corpus_image")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create audio corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusImageInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Image Corpus")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # corpus image info popup
        driver.find_element_by_id("add_id_corpusImageInfo").click()
        driver.switch_to_window("id_corpusImageInfo")
        # corpus image info / size popup
        driver.find_element_by_name("sizeinfotype_model_set-0-size").clear()
        driver.find_element_by_name("sizeinfotype_model_set-0-size").send_keys("100")
        driver.find_element_by_name("sizeinfotype_model_set-0-sizeUnit").send_keys("Gb")
        # save and close corpus image info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)
        
        # save image corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Image Corpus\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)

        
    def test_LR_creation_corpus_text_numerical(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_corpus_text_numerical")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create audio corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusTextNumericalInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Text Numerical Corpus")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # TODO check if this behaviour is normal
        # corpus text numerical info popup
        driver.find_element_by_id("add_id_corpusTextNumericalInfo").click()
        driver.switch_to_window("id_corpusTextNumericalInfo")
        # save and close corpus text numerical info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # save text numerical corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Text Numerical Corpus\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)

        
    def test_LR_creation_corpus_ngram(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_corpus_ngram")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create audio corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusTextNgramInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Ngram Corpus")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # corpus ngram info popup
        driver.find_element_by_id("add_id_corpusTextNgramInfo").click()
        driver.switch_to_window("id_corpusTextNgramInfo")
        # corpus ngram info / base item
        #driver.find_element_by_name("form-0-baseItem_old").send_keys("Other")
        Select(driver.find_element_by_name("form-0-baseItem_old")).select_by_visible_text("Other")
        driver.find_element_by_xpath("//a[@class='selector-add']").click()
        # corpus ngram info / order
        driver.find_element_by_name("form-0-order").clear()
        driver.find_element_by_name("form-0-order").send_keys("5")
        # corpus ngram info / linguality type
        Select(driver.find_element_by_id("id_form-2-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # corpus ngram info / language
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # corpus ngram info / size popup
        driver.find_element_by_name("sizeinfotype_model_set-0-size").clear()
        driver.find_element_by_name("sizeinfotype_model_set-0-size").send_keys("100")
        driver.find_element_by_name("sizeinfotype_model_set-0-sizeUnit").send_keys("Gb")
        # save and close corpus ngram info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)
        
        # save ngram corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Ngram Corpus\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)

        
    def test_LR_creation_lang_descr_text(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_lang_descr_text")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
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
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # language description general info popup
        driver.find_element_by_id("edit_id_langdescInfo").click()
        driver.switch_to_window("edit_id_langdescInfo")
        Select(driver.find_element_by_id("id_languageDescriptionType")).select_by_visible_text(
          "Grammar")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
        save_and_close(driver, root_id)
          
        # language description info text popup
        driver.find_element_by_id("add_id_languageDescriptionTextInfo").click()
        driver.switch_to_window("id_languageDescriptionTextInfo")
        Select(driver.find_element_by_id("id_form-2-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # language description info text / language
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # save and close language description info text popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # save language description text
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Text Language Description\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)
        
        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        

    def test_LR_creation_lang_descr_video(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_lang_descr_video")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create language description
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(
          "Language description")
        driver.find_element_by_id("id_langdescVideoInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Video Language Description")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # language description general info popup
        driver.find_element_by_id("edit_id_langdescInfo").click()
        driver.switch_to_window("edit_id_langdescInfo")
        Select(driver.find_element_by_id("id_languageDescriptionType")).select_by_visible_text(
          "Grammar")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
        save_and_close(driver, root_id)
          
        # language description info text popup
        driver.find_element_by_id("add_id_languageDescriptionTextInfo").click()
        driver.switch_to_window("id_languageDescriptionTextInfo")
        Select(driver.find_element_by_id("id_form-2-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # language description info text / language
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # save and close language description info text popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # language description info video popup
        driver.find_element_by_id("add_id_languageDescriptionVideoInfo").click()
        driver.switch_to_window("id_languageDescriptionVideoInfo")
        Select(driver.find_element_by_id("id_linktoothermediainfotype_model_set-0-otherMedia")) \
          .select_by_visible_text("Audio")
        # save and close language description info video popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # save language description text - video
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Video Language Description\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)
        
        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        

    def test_LR_creation_lang_descr_image(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_lang_descr_image")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create language description
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(
          "Language description")
        driver.find_element_by_id("id_langdescImageInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Image Language Description")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # language description general info popup
        driver.find_element_by_id("edit_id_langdescInfo").click()
        driver.switch_to_window("edit_id_langdescInfo")
        Select(driver.find_element_by_id("id_languageDescriptionType")).select_by_visible_text(
          "Grammar")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
        save_and_close(driver, root_id)
          
        # language description info text popup
        driver.find_element_by_id("add_id_languageDescriptionTextInfo").click()
        driver.switch_to_window("id_languageDescriptionTextInfo")
        Select(driver.find_element_by_id("id_form-2-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # language description info text / language
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # save and close language description info text popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # language description info image popup
        driver.find_element_by_id("add_id_languageDescriptionImageInfo").click()
        driver.switch_to_window("id_languageDescriptionImageInfo")
        Select(driver.find_element_by_id("id_linktoothermediainfotype_model_set-0-otherMedia")) \
          .select_by_visible_text("Audio")
        # save and close language description info video popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # save language description text - image
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Image Language Description\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)
        
        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        

    def test_LR_creation_lex_resource_text(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_lex_resource_text")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
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
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # lexical resource general info popup
        driver.find_element_by_id("edit_id_lexiconInfo").click()
        driver.switch_to_window("edit_id_lexiconInfo")
        Select(driver.find_element_by_id("id_lexicalConceptualResourceType")).select_by_visible_text(
          "Word List")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
        save_and_close(driver, root_id)
          
        # lexical resource text info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceTextInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceTextInfo")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # lexical resource text info / language
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # lexical resource text info / size
        _fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
        # save and close lexical resource text info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # save lexical resource text
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Lexical Resource Text\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        
        
    def test_LR_creation_lex_resource_audio(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_lex_resource_audio")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create lexical resource
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(
          "Lexical conceptual resource")
        driver.find_element_by_id("id_lexiconAudioInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Lexical Resource Audio")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # lexical resource general info popup
        driver.find_element_by_id("edit_id_lexiconInfo").click()
        driver.switch_to_window("edit_id_lexiconInfo")
        Select(driver.find_element_by_id("id_lexicalConceptualResourceType")).select_by_visible_text(
          "Word List")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
        save_and_close(driver, root_id)
          
        # lexical resource text info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceTextInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceTextInfo")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # lexical resource text info / language
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # lexical resource text info / size
        _fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
        # save and close lexical resource text info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # lexical resource audio info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceAudioInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceAudioInfo")
        # save and close lexical resource text info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # save lexical resource text - audio
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Lexical Resource Audio\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        
        
    def test_LR_creation_lex_resource_video(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_lex_resource_video")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create lexical resource
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(
          "Lexical conceptual resource")
        driver.find_element_by_id("id_lexiconVideoInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Lexical Resource Video")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # lexical resource general info popup
        driver.find_element_by_id("edit_id_lexiconInfo").click()
        driver.switch_to_window("edit_id_lexiconInfo")
        Select(driver.find_element_by_id("id_lexicalConceptualResourceType")).select_by_visible_text(
          "Word List")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
        save_and_close(driver, root_id)
          
        # lexical resource text info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceTextInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceTextInfo")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # lexical resource text info / language
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # lexical resource text info / size
        _fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
        # save and close lexical resource text info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # lexical resource video info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceVideoInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceVideoInfo")
        driver.find_element_by_name("form-2-0-typeOfVideoContent").send_keys("Other")
        # save and close lexical resource video info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # save lexical resource text - video
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Lexical Resource Video\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        
        
    def test_LR_creation_lex_resource_image(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_lex_resource_image")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        # create lexical resource
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(
          "Lexical conceptual resource")
        driver.find_element_by_id("id_lexiconImageInfo").click()
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
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Lexical Resource Image")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
        # lexical resource general info popup
        driver.find_element_by_id("edit_id_lexiconInfo").click()
        driver.switch_to_window("edit_id_lexiconInfo")
        Select(driver.find_element_by_id("id_lexicalConceptualResourceType")).select_by_visible_text(
          "Word List")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
        save_and_close(driver, root_id)
          
        # lexical resource text info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceTextInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceTextInfo")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # lexical resource text info / language
        _fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # lexical resource text info / size
        _fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
        # save and close lexical resource text info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # lexical resource image info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceImageInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceImageInfo")
        # save and close lexical resource video info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # save lexical resource text - image
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Lexical Resource Image\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # check the editor group of the resource is the default editor group of the user
        self.assertEqual(self.test_editor_group.name, 
          driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[5]").text)

        # make sure an internal resource cannot be published
        _publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        _ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        _publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        _delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)


    def test_error_messages_LR_creation(self):
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_corpus_text")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))

        # Tests for TEXT CORPUS
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusTextInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save text corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Add Corpus Text Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1/a[@class='error']").text)

        # corpus text info popup
        driver.find_element_by_id("add_id_corpusTextInfo-0").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='size']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='sizeUnit']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for AUDIO CORPUS
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusAudioInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save Audio corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Add Corpus Audio Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1/a[@class='error']").text)

        # corpus audio info popup
        driver.find_element_by_id("add_id_corpusAudioInfo").click()
        driver.switch_to_window("id_corpusAudioInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row audioSizeInfo']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for VIDEO CORPUS
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusVideoInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save Video corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Add Corpus Video Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1/a[@class='error']").text)

        # corpus video info popup
        driver.find_element_by_id("add_id_corpusVideoInfo-0").click()
        driver.switch_to_window("id_corpusVideoInfo__dash__0")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='size']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='sizeUnit']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for IMAGE CORPUS
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusImageInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save Image corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Add Corpus Image Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1/a[@class='error']").text)

        # corpus image info popup
        driver.find_element_by_id("add_id_corpusImageInfo").click()
        driver.switch_to_window("id_corpusImageInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='size']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='sizeUnit']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for TEXT NUMERICAL CORPUS
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusTextNumericalInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save text numerical corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_continue(driver, root_id)

        # Tests for TEXT N-GRAM CORPUS
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusTextNgramInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save text n-gram corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Add Corpus Text N-gram Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1/a[@class='error']").text)

        # corpus text n-gram info popup
        driver.find_element_by_id("add_id_corpusTextNgramInfo").click()
        driver.switch_to_window("id_corpusTextNgramInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors baseItem']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors order']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='size']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='sizeUnit']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for TEXT LANGUAGE DESCRIPTION
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Language description")
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save text language description
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Edit Language Description General Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[1]/a[@class='error']").text)
        self.assertEqual("Add Language Description Text Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[2]/a[@class='error']").text)

        # corpus general info popup
        driver.find_element_by_id("edit_id_langdescInfo").click()
        driver.switch_to_window("edit_id_langdescInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row languageDescriptionType']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus text info popup
        driver.find_element_by_id("add_id_languageDescriptionTextInfo").click()
        driver.switch_to_window("id_languageDescriptionTextInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for VIDEO LANGUAGE DESCRIPTION
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Language description")
        driver.find_element_by_id("id_langdescVideoInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save video language description
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Edit Language Description General Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[1]/a[@class='error']").text)
        self.assertEqual("Add Language Description Text Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[2]/a[@class='error']").text)
        self.assertEqual("Add Language Description Video Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[3]/a[@class='error']").text)

        # corpus general info popup
        driver.find_element_by_id("edit_id_langdescInfo").click()
        driver.switch_to_window("edit_id_langdescInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row languageDescriptionType']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus text info popup
        driver.find_element_by_id("add_id_languageDescriptionTextInfo").click()
        driver.switch_to_window("id_languageDescriptionTextInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus video info popup
        driver.find_element_by_id("add_id_languageDescriptionVideoInfo").click()
        driver.switch_to_window("id_languageDescriptionVideoInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors otherMedia']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for IMAGE LANGUAGE DESCRIPTION
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Language description")
        driver.find_element_by_id("id_langdescImageInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save image language description
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Edit Language Description General Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[1]/a[@class='error']").text)
        self.assertEqual("Add Language Description Text Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[2]/a[@class='error']").text)
        self.assertEqual("Add Language Description Image Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[3]/a[@class='error']").text)

        # corpus general info popup
        driver.find_element_by_id("edit_id_langdescInfo").click()
        driver.switch_to_window("edit_id_langdescInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row languageDescriptionType']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus text info popup
        driver.find_element_by_id("add_id_languageDescriptionTextInfo").click()
        driver.switch_to_window("id_languageDescriptionTextInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus image info popup
        driver.find_element_by_id("add_id_languageDescriptionImageInfo").click()
        driver.switch_to_window("id_languageDescriptionImageInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors otherMedia']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for TEXT LEXICAL CONCEPTUAL RESOURCE
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Lexical conceptual resource")
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save text lexical conceptual resource
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Edit Lexical Conceptual Resource General Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[1]/a[@class='error']").text)
        self.assertEqual("Add Lexical Conceptual Resource Text Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[2]/a[@class='error']").text)

        # corpus general info popup
        driver.find_element_by_id("edit_id_lexiconInfo").click()
        driver.switch_to_window("edit_id_lexiconInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row lexicalConceptualResourceType']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus text info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceTextInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceTextInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='size']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='sizeUnit']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for AUDIO LEXICAL CONCEPTUAL RESOURCE
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Lexical conceptual resource")
        driver.find_element_by_id("id_lexiconAudioInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save audio lexical conceptual resource
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Edit Lexical Conceptual Resource General Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[1]/a[@class='error']").text)
        self.assertEqual("Add Lexical Conceptual Resource Text Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[2]/a[@class='error']").text)
        self.assertEqual("Add Lexical Conceptual Resource Audio Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[3]/a[@class='error']").text)

        # corpus general info popup
        driver.find_element_by_id("edit_id_lexiconInfo").click()
        driver.switch_to_window("edit_id_lexiconInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row lexicalConceptualResourceType']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus text info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceTextInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceTextInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='size']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='sizeUnit']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for VIDEO LEXICAL CONCEPTUAL RESOURCE
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Lexical conceptual resource")
        driver.find_element_by_id("id_lexiconVideoInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save video lexical conceptual resource
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Edit Lexical Conceptual Resource General Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[1]/a[@class='error']").text)
        self.assertEqual("Add Lexical Conceptual Resource Text Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[2]/a[@class='error']").text)
        self.assertEqual("Add Lexical Conceptual Resource Video Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[3]/a[@class='error']").text)

        # corpus general info popup
        driver.find_element_by_id("edit_id_lexiconInfo").click()
        driver.switch_to_window("edit_id_lexiconInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row lexicalConceptualResourceType']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus text info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceTextInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceTextInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='size']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='sizeUnit']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus video info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceVideoInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceVideoInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors typeOfVideoContent']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for IMAGE LEXICAL CONCEPTUAL RESOURCE
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Lexical conceptual resource")
        driver.find_element_by_id("id_lexiconImageInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save image lexical conceptual resource
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Edit Lexical Conceptual Resource General Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[1]/a[@class='error']").text)
        self.assertEqual("Add Lexical Conceptual Resource Text Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[2]/a[@class='error']").text)
        self.assertEqual("Add Lexical Conceptual Resource Image Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[3]/a[@class='error']").text)

        # corpus general info popup
        driver.find_element_by_id("edit_id_lexiconInfo").click()
        driver.switch_to_window("edit_id_lexiconInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row lexicalConceptualResourceType']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)

        # corpus text info popup
        driver.find_element_by_id("add_id_lexicalConceptualResourceTextInfo").click()
        driver.switch_to_window("id_lexicalConceptualResourceTextInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors lingualityType']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageId']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors languageName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='size']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//tr[@id='sizeinfotype_model_set-0']/td[@class='sizeUnit']/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)

        # Tests for TEXT LEXICAL CONCEPTUAL RESOURCE
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        #Select resource type
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Tool / Service")
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # remember root window id
        root_id = driver.current_window_handle

        # save tool / service resource
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()

        self.assertEqual("Please correct the errors below.", driver.find_element_by_xpath(
          "//p[@class='errornote']").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors resourceName']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row errors description']/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row distributionInfo']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row contactPerson']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        self.assertEqual("Edit Tool / Service Info", driver.find_element_by_xpath(
          "//div[@id='contentInfoStuff']/h1[1]/a[@class='error']").text)

        # corpus tool / service info popup
        driver.find_element_by_id("edit_id_toolServiceInfo").click()
        driver.switch_to_window("edit_id_toolServiceInfo")
        driver.find_element_by_name("_save").click()
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row toolServiceType']/div/ul/li[1]").text)
        self.assertEqual("This field is required.", driver.find_element_by_xpath(
          "//div[@class='form-row languageDependent']/div/ul/li[1]").text)
        self.assertEqual("Required", driver.find_element_by_xpath(
          "//div[@id='firstlevel']/div[@class='fields']/ul/li[1]/a[@class='error']").text)
        cancel_and_close(driver, root_id)
        cancel_and_continue(driver, root_id)
