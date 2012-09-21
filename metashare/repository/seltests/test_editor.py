from django_selenium.testcases import SeleniumTestCase
from metashare import settings, test_utils
from metashare.accounts.models import EditorGroup, EditorGroupManagers
from metashare.repository.models import resourceInfoType_model
from metashare.repository.seltests.test_utils import login_user, mouse_over, \
    setup_screenshots_folder, click_menu_item, save_and_close, cancel_and_close, \
    cancel_and_continue
from metashare.settings import DJANGO_BASE, ROOT_PATH
from selenium.webdriver.support.ui import Select
import time
from django.core.management import call_command


TESTFIXTURE_XML = '{}/repository/fixtures/ILSP10.xml'.format(ROOT_PATH)

class EditorTest(SeleniumTestCase):
    
    
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

        # create an editor user
        test_utils.create_editor_user('editoruser', 'editor@example.com',
                                      'secret', (self.test_editor_group,))
        # make sure the index does not contain any stale entries
        call_command('rebuild_index', interactive=False, using=settings.TEST_MODE_NAME)

        super(EditorTest, self).setUp()
        self.base_url = 'http://{}:{}/{}' \
            .format(self.testserver_host, self.testserver_port, DJANGO_BASE)
        self.verification_errors = []


    def tearDown(self):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()

        super(EditorTest, self).tearDown()
        self.assertEqual([], self.verification_errors)


    def test_status_after_saving(self):
        
        # load test fixture and set its status to 'published'
        test_utils.setup_test_storage()
        _result = test_utils.import_xml(TESTFIXTURE_XML)
        resource = resourceInfoType_model.objects.get(pk=_result.id)
        resource.editor_groups.add(self.test_editor_group)
        resource.storage_object.published = True
        # this also saves the storage object:
        resource.save()
    
        driver = self.driver
        driver.get(self.base_url)
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        # make sure we are on the right site
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
        # corpus text info popup
        driver.find_element_by_id("add_id_corpusTextInfo-0").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # corpus text info / language
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # corpus text info / size
        self.fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
        # corpus audio info popup
        driver.find_element_by_id("add_id_corpusAudioInfo").click()
        driver.switch_to_window("id_corpusAudioInfo")
        Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
          "Monolingual")
        # corpus audio info / language
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # corpus audio info / size popup
        driver.find_element_by_css_selector("#add_id_audioSizeInfo > img[alt=\"Add Another\"]").click()
        self.fill_audio_size(driver, ss_path, "id_corpusAudioInfo")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # lexical resource text info / size
        self.fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # lexical resource text info / size
        self.fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # lexical resource text info / size
        self.fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
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
        self.fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        self.fill_contact_person(driver, ss_path, root_id)
        
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
        self.fill_language(driver, ss_path, "languageinfotype_model_set-0-")
        # lexical resource text info / size
        self.fill_text_size(driver, ss_path, "sizeinfotype_model_set-0-")
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
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        
        
    def test_LR_creation_tool(self):
        # set up the current manager user profile so that it doesn't have any
        # default editor groups
        self.manager_user.get_profile().default_editor_groups.clear()

        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_tool")
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
        # (add an invalid character in the resource name to verify that invalid
        # characters are found in DictField values)
        driver.find_element_by_name("key_form-0-resourceName_0").clear()
        driver.find_element_by_name("key_form-0-resourceName_0").send_keys("en")
        driver.find_element_by_name("val_form-0-resourceName_0").clear()
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys(u"Test\u000b Tool")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
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
        Select(driver.find_element_by_id("id_toolServiceType")).select_by_visible_text("Tool")
        Select(driver.find_element_by_id("id_languageDependent")).select_by_visible_text("Yes")
        # save and close tool info popup
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, root_id)

        # add both optional "Identifier" and "Original metadata schema" fields
        # (add an invalid character here to verify that invalid characters are
        # found in both MultiTextField values and in XmlCharField values)
        _identifier_elem = \
            driver.find_element_by_xpath("//ul[@id='widget_1']/li[1]/input")
        _identifier_elem.clear()
        _identifier_elem.send_keys(u"test \u0007identifier")
        driver.find_element_by_id("id_form-2-0-originalMetadataSchema").clear()
        driver.find_element_by_id("id_form-2-0-originalMetadataSchema") \
            .send_keys(u"test metadata schema \u0016A")

        # save tool - we expect three error messages due to the invalid
        # characters in some fields:
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertTrue(driver.find_element_by_xpath(
            "//div[@id='form-0']/fieldset/div/ul/li").text.startswith(
                "The character at position 5 (&#x000b;) must not be used."))
        self.assertTrue(driver.find_element_by_xpath(
            "//ul[@id='widget_1']/li[1]/small").text.startswith(
                "The character at position 6 (&#x0007;) must not be used."))
        self.assertTrue(driver.find_element_by_xpath(
            "//div[@id='form-2-0']/fieldset/div[3]/ul/li").text.startswith(
                "The character at position 22 (&#x0016;) must not be used."))
        # correct the resource name now
        driver.find_element_by_name("val_form-0-resourceName_0").clear()
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Tool")
        # correct the optional "Identifier" field now
        _identifier_elem = \
            driver.find_element_by_xpath("//ul[@id='widget_1']/li[1]/input")
        _identifier_elem.clear()
        _identifier_elem.send_keys(u"test identifier")
        # correct the optional "Original metadata schema" field now
        driver.find_element_by_id("id_form-2-0-originalMetadataSchema").clear()
        driver.find_element_by_id("id_form-2-0-originalMetadataSchema") \
            .send_keys(u"test metadata schema")

        # save tool
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("_save").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("The Resource \"Test Tool\" was added successfully.", 
          driver.find_element_by_css_selector("li.info").text)

        # make sure that the editor groups list of the created resource is empty
        # (which resembles the default editor groups list of the creating user)
        _created_res = resourceInfoType_model.objects.get(pk=1)
        self.assertEqual(0, _created_res.editor_groups.count(),
            'the created resource must not have any editor groups (just like ' \
                'the default groups set of the creating user)')
        # for the following tests to not fail, we have to add the resource to an
        # editor group again which is managed by the current user
        _created_res.editor_groups.add(self.test_editor_group)

        # make sure an internal resource cannot be published
        self.publish(driver)
        self.assertEqual("internal",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Only ingested resources can be published.", 
         driver.find_element_by_css_selector("ul.messagelist>li.error").text)
        # ingest resource
        self.ingest(driver)
        self.assertEqual("ingested",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully ingested 1 internal resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # publish resource
        self.publish(driver)
        self.assertEqual("published",
         driver.find_element_by_xpath("//table[@id='result_list']/tbody/tr[1]/td[3]").text)
        self.assertEqual("Successfully published 1 ingested resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)
        # delete resource
        self.delete(driver)
        self.assertEqual("Successfully deleted 1 resource.", 
         driver.find_element_by_css_selector("ul.messagelist>li").text)


    def test_sorting(self):
        """
        tests the sorting of controlled vocabulary in some examplary CharFields
        used in the Editor
        """
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "sorting")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "editoruser", "secret")
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
        self.assertEqual("Available - Restricted Use", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[2]").text)
        self.assertEqual("Available - Unrestricted Use", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[3]").text)
        self.assertEqual("Not Available Through Meta Share", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[4]").text)        
        self.assertEqual("Under Negotiation", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[5]").text)
        save_and_close(driver, root_id)
        # corpus info text popup
        driver.find_element_by_id("add_id_corpusTextInfo-0").click()
        driver.switch_to_window("id_corpusTextInfo__dash__0")
        # check sorting of Linguality
        self.assertEqual("Bilingual", driver.find_element_by_xpath(
          "//select[@id='id_form-0-lingualityType']/option[2]").text)
        self.assertEqual("Monolingual", driver.find_element_by_xpath(
          "//select[@id='id_form-0-lingualityType']/option[3]").text)
        self.assertEqual("Multilingual", driver.find_element_by_xpath(
          "//select[@id='id_form-0-lingualityType']/option[4]").text)
        # check sorting of Size unit
        self.assertEqual("4 - Grams", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[2]").text)
        self.assertEqual("5 - Grams", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[3]").text)
        self.assertEqual("Articles", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[4]").text)
        self.assertEqual("Bigrams", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[5]").text)
        self.assertEqual("Bytes", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[6]").text)
        self.assertEqual("Classes", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[7]").text)
        self.assertEqual("Concepts", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[8]").text)                                        
        self.assertEqual("Diphones", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[9]").text)
        self.assertEqual("Elements", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[10]").text)    
        # skip to end of list 
        self.assertEqual("Words", driver.find_element_by_xpath(
          "//select[@id='id_sizeinfotype_model_set-0-sizeUnit']/option[50]").text)        

    
    def test_multi_select_widget(self):
        """
        tests the usage of the FilteredSelectMultiple widget for multi select fields
        """
        driver = self.driver
        driver.get(self.base_url)
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "multi_select_widget")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "editoruser", "secret")
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
        # create text corpus
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text("Corpus")
        driver.find_element_by_id("id_corpusTextInfo").click()
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text)
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        driver.switch_to_window("id_distributionInfo")
        # show licenses
        driver.find_element_by_id("fieldsetcollapser0").click()
        # check that the left window contains all entries
        self.assertEqual("Under Negotiation", driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_from']/option[41]").text)
        # add an entry
        driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_from']/option[1]").click()
        driver.find_element_by_link_text("Add").click()
        # check that entry has moved to right site
        self.assertEqual("AGPL", driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_to']/option[1]").text)
        self.assertEqual("Apache Licence_V2.0", driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_from']/option[1]").text)
        # remove entry
        driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_to']/option[1]").click()
        driver.find_element_by_link_text("Remove").click()
        # entry is now at last position on left site
        self.assertEqual("AGPL", driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_from']/option[41]").text)
        
        
    def fill_distribution(self, driver, ss_path, parent_id):
        """
        fills the distribution popup with required information and returns
        to the parent window
        """
        driver.switch_to_window("id_distributionInfo")
        Select(driver.find_element_by_id("id_availability")).select_by_visible_text(
          "Available - Unrestricted Use")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        save_and_close(driver, parent_id)
        
        
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
        save_and_close(driver, parent_id)
        
        
    def fill_language(self, driver, ss_path, id_infix):
        """
        fills the language with required information
        """
        driver.find_element_by_id("id_{}languageId".format(id_infix)).clear()
        driver.find_element_by_id("id_{}languageId".format(id_infix)).send_keys("De")
        driver.find_element_by_id("id_{}languageName".format(id_infix)).clear()
        driver.find_element_by_id("id_{}languageName".format(id_infix)).send_keys("German")
        
        
    def fill_text_size(self, driver, ss_path, id_infix):
        """
        fills the text size with required information
        """
        driver.find_element_by_id("id_{}size".format(id_infix)).clear()
        driver.find_element_by_id("id_{}size".format(id_infix)).send_keys("10000")
        Select(driver.find_element_by_id("id_{}sizeUnit".format(id_infix))).select_by_visible_text("Tokens")
        
        
    def fill_audio_size(self, driver, ss_path, parent_id):
        """
        fills the text size with required information
        """
        driver.switch_to_window("id_audioSizeInfo")

        driver.find_element_by_id("id_sizeinfotype_model_set-0-size").send_keys("100")
        
        Select(driver.find_element_by_id("id_sizeinfotype_model_set-0-sizeUnit")).select_by_visible_text("Gb")
        save_and_close(driver, parent_id) 
        
        
    def ingest(self, driver):
        """
        selects all resources and ingests them
        """
        driver.find_element_by_id("action-toggle").click()
        Select(driver.find_element_by_name("action")).select_by_visible_text("Ingest selected internal resources")
        driver.find_element_by_name("index").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)

        
    def publish(self, driver):
        """
        selects all resources and publishes them
        """
        driver.find_element_by_id("action-toggle").click()
        Select(driver.find_element_by_name("action")).select_by_visible_text("Publish selected ingested resources")
        driver.find_element_by_name("index").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)
        
    def delete(self, driver):
        """
        selects all resources and deletes them
        """
        driver.find_element_by_id("action-toggle").click()
        Select(driver.find_element_by_name("action")).select_by_visible_text("Mark selected resources as deleted")
        driver.find_element_by_name("index").click()
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        # TODO remove this workaround when Selenium starts working again as intended
        time.sleep(1)


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
