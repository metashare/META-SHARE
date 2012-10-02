import time

from django.core.management import call_command
from django_selenium.testcases import SeleniumTestCase

from selenium.webdriver.support.ui import Select

from metashare import settings, test_utils
from metashare.accounts.models import EditorGroup, EditorGroupManagers
from metashare.repository.models import resourceInfoType_model
from metashare.repository.seltests.test_utils import login_user, mouse_over, \
    setup_screenshots_folder, click_menu_item, save_and_close
from metashare.settings import DJANGO_BASE, ROOT_PATH


TESTFIXTURE_XML = '{}/repository/fixtures/ILSP10.xml'.format(ROOT_PATH)


class BasicEditorTests(SeleniumTestCase):
    """
    Basic tests for the metadata editor which are meant to be run in every
    Jenkins build.
    
    The test case contains only one full LR creation test (for a tool/service
    LR); other LR creation tests can be found in the `NightlyEditorTests` test
    case.
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

        # create an editor user
        test_utils.create_editor_user('editoruser', 'editor@example.com',
                                      'secret', (self.test_editor_group,))
        # make sure the index does not contain any stale entries
        call_command('rebuild_index', interactive=False,
                     using=settings.TEST_MODE_NAME)

        super(BasicEditorTests, self).setUp()
        self.base_url = 'http://{}:{}/{}' \
            .format(self.testserver_host, self.testserver_port, DJANGO_BASE)
        self.verification_errors = []


    def tearDown(self):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()

        super(BasicEditorTests, self).tearDown()
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
        self.assertEqual("Logout", driver.find_element_by_xpath(
                "//div[@id='inner']/div[2]/a/div").text)
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        click_menu_item(driver,
            driver.find_element_by_link_text("Manage all resources"))
        # make sure we are on the right site
        self.assertEqual("Select Resource to change | META-SHARE backend",
            driver.title)
        # check if LR entry is available and that its status is published
        try: 
            self.assertEqual("REVEAL-THIS Corpus",
                driver.find_element_by_link_text("REVEAL-THIS Corpus").text)
        except AssertionError as e: 
            self.verification_errors.append(str(e))
        try: 
            self.assertEqual("published",
                driver.find_element_by_xpath(
                    "//table[@id='result_list']/tbody/tr/td[3]").text)
        except AssertionError as e: 
            self.verification_errors.append(str(e))
        # click LR to edit it
        driver.find_element_by_link_text("REVEAL-THIS Corpus").click()
        # change the short name and save the LR
        driver.find_element_by_name("key_form-0-resourceShortName_0").clear()
        driver.find_element_by_name("key_form-0-resourceShortName_0") \
            .send_keys("en")
        driver.find_element_by_name("val_form-0-resourceShortName_0").clear()
        driver.find_element_by_name("val_form-0-resourceShortName_0") \
            .send_keys("a random short name")
        driver.find_element_by_name("_save").click()
        # make sure that the LR status is still published after saving
        try: 
            self.assertEqual("published", 
                driver.find_element_by_xpath(
                    "//table[@id='result_list']/tbody/tr/td[3]").text)
        except AssertionError as e: 
            self.verification_errors.append(str(e))


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
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        
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
            driver.find_element_by_xpath("//ul[@id='widget_2']/li[1]/input")
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
            "//ul[@id='widget_2']/li[1]/small").text.startswith(
                "The character at position 6 (&#x0007;) must not be used."))
        self.assertTrue(driver.find_element_by_xpath(
            "//div[@id='form-2-0']/fieldset/div[3]/ul/li").text.startswith(
                "The character at position 22 (&#x0016;) must not be used."))
        # correct the resource name now
        driver.find_element_by_name("val_form-0-resourceName_0").clear()
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys("Test Tool")
        # correct the optional "Identifier" field now
        _identifier_elem = \
            driver.find_element_by_xpath("//ul[@id='widget_2']/li[1]/input")
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
          "//select[@id='id_licenceinfotype_model_set-0-licence_from']/option[39]").text)
        # add an entry
        driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_from']/option[1]").click()
        driver.find_element_by_link_text("Add").click()
        # check that entry has moved to right site
        self.assertEqual("AGPL", driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_to']/option[1]").text)
        self.assertEqual("Apache Licence_2.0", driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_from']/option[1]").text)
        # remove entry
        driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_to']/option[1]").click()
        driver.find_element_by_link_text("Remove").click()
        # entry is now at last position on left site
        self.assertEqual("AGPL", driver.find_element_by_xpath(
          "//select[@id='id_licenceinfotype_model_set-0-licence_from']/option[39]").text)


    def test_full_LR_creation_corpus_text(self):
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
        driver.find_element_by_xpath("//div[@class='form-row resourceShortName']/div/ul/li/a").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("key_form-0-resourceShortName_0").clear()
        driver.find_element_by_name("key_form-0-resourceShortName_0").send_keys("en")
        driver.find_element_by_name("val_form-0-resourceShortName_0").clear()
        driver.find_element_by_name("val_form-0-resourceShortName_0").send_keys("TTC")
        driver.find_element_by_name("form-0-url").clear()
        driver.find_element_by_name("form-0-url").send_keys("http://www.ttc.org")
        driver.find_element_by_name("form-0-identifier").clear()
        driver.find_element_by_name("form-0-identifier").send_keys("A-123")
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
        _fill_distribution(driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contact_person(driver, ss_path, root_id)
        # contact metadata creator popup
        driver.find_element_by_xpath("//a[@id='add_id_form-2-0-metadataCreator']/img").click()
        _fill_metadata_creator(driver, ss_path, root_id)
        driver.find_element_by_name("form-2-0-source").clear()
        driver.find_element_by_name("form-2-0-source").send_keys("catalogue")
        driver.find_element_by_name("form-2-0-originalMetadataSchema").clear()
        driver.find_element_by_name("form-2-0-originalMetadataSchema").send_keys("metadata")
        driver.find_element_by_name("form-2-0-originalMetadataLink").clear()
        driver.find_element_by_name("form-2-0-originalMetadataLink").send_keys("http://catalogue.org/ttc")
        driver.find_element_by_name("form-2-0-metadataLanguageName").clear()
        driver.find_element_by_name("form-2-0-metadataLanguageName").send_keys("english")
        driver.find_element_by_name("form-2-0-metadataLanguageId").clear()
        driver.find_element_by_name("form-2-0-metadataLanguageId").send_keys("en")
        driver.find_element_by_name("form-2-0-revision").clear()
        driver.find_element_by_name("form-2-0-revision").send_keys("1.0")

        # recommended page
        driver.find_element_by_css_selector("a[href=\"#field-2\"]").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        driver.find_element_by_name("form-3-0-version").clear()
        driver.find_element_by_name("form-3-0-version").send_keys("1.0")
        driver.find_element_by_name("form-3-0-revision").clear()
        driver.find_element_by_name("form-3-0-revision").send_keys("1.0")
        driver.find_element_by_name("form-3-0-lastDateUpdated").clear()
        driver.find_element_by_name("form-3-0-lastDateUpdated").send_keys("2012-09-28")
        driver.find_element_by_name("form-3-0-updateFrequency").clear()
        driver.find_element_by_name("form-3-0-updateFrequency").send_keys("1")
        # usage popup
        driver.find_element_by_xpath("//a[@id='add_id_usageInfo']/img").click()  
        _fill_usage(driver, ss_path, root_id)
        # documentation popup
        Select(driver.find_element_by_xpath("//div[@class='form-row documentation']/div/select")).select_by_visible_text("documentInfoType")
        _fill_documentation(driver, ss_path, root_id)
        driver.find_element_by_name("form-4-0-samplesLocation").clear()
        driver.find_element_by_name("form-4-0-samplesLocation").send_keys("http://ttc.samples.org")
        Select(driver.find_element_by_name(
          "form-4-0-toolDocumentationType_old")).select_by_visible_text("Manual")
        driver.find_element_by_xpath("//div[@class='form-row toolDocumentationType']/div/div/div/a") \
          .click()
        # resource creator popup
        Select(driver.find_element_by_xpath("//div[@class='form-row resourceCreator']/div/select")).select_by_visible_text("personInfoType")
        _fill_resource_creator(driver, ss_path, root_id)
        # funding project popup
        driver.find_element_by_xpath("//a[@id='add_id_form-5-0-fundingProject']/img").click()  
        _fill_funding_project(driver, ss_path, root_id)
        driver.find_element_by_name("form-5-0-creationStartDate").clear()
        driver.find_element_by_name("form-5-0-creationStartDate").send_keys("2012-09-28")
        driver.find_element_by_name("form-5-0-creationEndDate").clear()
        driver.find_element_by_name("form-5-0-creationEndDate").send_keys("2012-09-28")
        # relations field
        driver.find_element_by_id("fieldsetcollapser1").click()
        driver.find_element_by_name("relationinfotype_model_set-0-relationType").clear()
        driver.find_element_by_name("relationinfotype_model_set-0-relationType").send_keys("new type")
        # related resource popup
        driver.find_element_by_xpath("//a[@id='add_id_relationinfotype_model_set-0-relatedResource']/img").click()  
        _fill_related_resource(driver, ss_path, root_id)
        
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


def _fill_distribution(driver, ss_path, parent_id):
    """
    fills the distribution popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_distributionInfo")
    # remember current window id
    current_id = driver.current_window_handle
    Select(driver.find_element_by_id("id_availability")).select_by_visible_text(
      "Available - Unrestricted Use")

    # licences
    driver.find_element_by_id("fieldsetcollapser0").click()
    Select(driver.find_element_by_name(
      "licenceinfotype_model_set-0-licence_old")).select_by_visible_text("AGPL")
    driver.find_element_by_xpath(
      "//div[@class='form-row licence']/div/div/ul/li/a") \
      .click()
    Select(driver.find_element_by_name(
      "licenceinfotype_model_set-0-restrictionsOfUse_old")).select_by_visible_text("Attribution")
    driver.find_element_by_xpath(
      "//div[@class='form-row restrictionsOfUse']/div/div/ul/li/a") \
      .click()
    Select(driver.find_element_by_name(
      "licenceinfotype_model_set-0-distributionAccessMedium_old")).select_by_visible_text("CD - ROM")
    driver.find_element_by_xpath(
      "//div[@class='form-row distributionAccessMedium']/div/div/ul/li/a") \
      .click()
    driver.find_element_by_name("licenceinfotype_model_set-0-downloadLocation").clear()
    driver.find_element_by_name("licenceinfotype_model_set-0-downloadLocation").send_keys("http://mylicence.org")
    driver.find_element_by_name("licenceinfotype_model_set-0-executionLocation").clear()
    driver.find_element_by_name("licenceinfotype_model_set-0-executionLocation").send_keys("http://myexecution.org")
    driver.find_element_by_name("licenceinfotype_model_set-0-fee").clear()
    driver.find_element_by_name("licenceinfotype_model_set-0-fee").send_keys("1.10")
    driver.find_element_by_xpath("//div[@class='form-row attributionText']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_licenceinfotype_model_set-0-attributionText_0").clear()
    driver.find_element_by_name("key_licenceinfotype_model_set-0-attributionText_0").send_keys("en")
    driver.find_element_by_name("val_licenceinfotype_model_set-0-attributionText_0").clear()
    driver.find_element_by_name("val_licenceinfotype_model_set-0-attributionText_0").send_keys("The attribution text.")
    Select(driver.find_element_by_xpath("//div[@class='form-row licensor']/div/select")).select_by_visible_text("personInfoType")
    _fill_licensor(driver, ss_path, current_id)
    Select(driver.find_element_by_xpath("//div[@class='form-row distributionRightsHolder']/div/select")).select_by_visible_text("personInfoType")
    _fill_distribution_rights_holder(driver, ss_path, current_id)
    Select(driver.find_element_by_name(
      "licenceinfotype_model_set-0-userNature_old")).select_by_visible_text("Academic")
    driver.find_element_by_xpath(
      "//div[@class='form-row userNature']/div/div/ul/li/a") \
      .click()
    driver.find_element_by_xpath("//a[@id='add_id_licenceinfotype_model_set-0-membershipInfo']/img").click()  
    _fill_membership(driver, ss_path, current_id)

    Select(driver.find_element_by_xpath("//div[@class='form-row iprHolder']/div/select")).select_by_visible_text("personInfoType")
    _fill_ipr_holder(driver, ss_path, current_id)
    driver.find_element_by_name("availabilityStartDate").clear()
    driver.find_element_by_name("availabilityStartDate").send_keys("2012-10-02")
    driver.find_element_by_name("availabilityEndDate").clear()
    driver.find_element_by_name("availabilityEndDate").send_keys("2012-10-02")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_contact_person(driver, ss_path, parent_id):
    """
    fills the contact person popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_contactPerson")
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("key_surname_0").clear()
    driver.find_element_by_name("key_surname_0").send_keys("en")
    driver.find_element_by_name("val_surname_0").clear()
    driver.find_element_by_name("val_surname_0").send_keys("Smith")
    driver.find_element_by_xpath("//div[@class='form-row givenName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_givenName_0").clear()
    driver.find_element_by_name("key_givenName_0").send_keys("en")
    driver.find_element_by_name("val_givenName_0").clear()
    driver.find_element_by_name("val_givenName_0").send_keys("John")
    Select(driver.find_element_by_id("id_sex")).select_by_visible_text("Male")
    driver.find_element_by_name("form-0-email").clear()
    driver.find_element_by_name("form-0-email").send_keys("john.smith@institution.org")
    driver.find_element_by_name("form-0-url").clear()
    driver.find_element_by_name("form-0-url").send_keys("http://www.institution.org")
    driver.find_element_by_name("form-0-address").clear()
    driver.find_element_by_name("form-0-address").send_keys("1st main street")
    driver.find_element_by_name("form-0-zipCode").clear()
    driver.find_element_by_name("form-0-zipCode").send_keys("95000")
    driver.find_element_by_name("form-0-city").clear()
    driver.find_element_by_name("form-0-city").send_keys("somewhere")
    driver.find_element_by_name("form-0-region").clear()
    driver.find_element_by_name("form-0-region").send_keys("far away")
    driver.find_element_by_name("form-0-country").clear()
    driver.find_element_by_name("form-0-country").send_keys("world")
    driver.find_element_by_name("form-0-telephoneNumber").clear()
    driver.find_element_by_name("form-0-telephoneNumber").send_keys("1234567890")
    driver.find_element_by_name("form-0-faxNumber").clear()
    driver.find_element_by_name("form-0-faxNumber").send_keys("1234567890")
    driver.find_element_by_name("position").clear()
    driver.find_element_by_name("position").send_keys("Professor")
    # affiliation popup
    driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
    _fill_affiliation(driver, ss_path, current_id)
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_affiliation(driver, ss_path, parent_id):
    """
    fills the affiliation popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_affiliation")
    driver.find_element_by_name("key_organizationName_0").clear()
    driver.find_element_by_name("key_organizationName_0").send_keys("en")
    driver.find_element_by_name("val_organizationName_0").clear()
    driver.find_element_by_name("val_organizationName_0").send_keys("Organization")
    driver.find_element_by_xpath("//div[@class='form-row organizationShortName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_organizationShortName_0").clear()
    driver.find_element_by_name("key_organizationShortName_0").send_keys("en")
    driver.find_element_by_name("val_organizationShortName_0").clear()
    driver.find_element_by_name("val_organizationShortName_0").send_keys("Short name")
    driver.find_element_by_xpath("//div[@class='form-row departmentName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_departmentName_0").clear()
    driver.find_element_by_name("key_departmentName_0").send_keys("en")
    driver.find_element_by_name("val_departmentName_0").clear()
    driver.find_element_by_name("val_departmentName_0").send_keys("Department")

    driver.find_element_by_name("form-0-email").clear()
    driver.find_element_by_name("form-0-email").send_keys("john.smith@institution.org")
    driver.find_element_by_name("form-0-url").clear()
    driver.find_element_by_name("form-0-url").send_keys("http://www.institution.org")
    driver.find_element_by_name("form-0-address").clear()
    driver.find_element_by_name("form-0-address").send_keys("1st main street")
    driver.find_element_by_name("form-0-zipCode").clear()
    driver.find_element_by_name("form-0-zipCode").send_keys("95000")
    driver.find_element_by_name("form-0-city").clear()
    driver.find_element_by_name("form-0-city").send_keys("somewhere")
    driver.find_element_by_name("form-0-region").clear()
    driver.find_element_by_name("form-0-region").send_keys("far away")
    driver.find_element_by_name("form-0-country").clear()
    driver.find_element_by_name("form-0-country").send_keys("world")
    driver.find_element_by_name("form-0-telephoneNumber").clear()
    driver.find_element_by_name("form-0-telephoneNumber").send_keys("1234567890")
    driver.find_element_by_name("form-0-faxNumber").clear()
    driver.find_element_by_name("form-0-faxNumber").send_keys("1234567890")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_usage(driver, ss_path, parent_id):
    """
    fills the usage popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_usageInfo")
    current_id = driver.current_window_handle
    # access tool popup
    driver.find_element_by_xpath("//a[@id='add_id_accessTool']/img").click()  
    _fill_access_tool(driver, ss_path, current_id)
     # resource associated with popup
    driver.find_element_by_xpath("//a[@id='add_id_resourceAssociatedWith']/img").click()  
    _fill_resource_associated_with(driver, ss_path, current_id)
    # foreseen use
    driver.find_element_by_id("fieldsetcollapser0").click()
    Select(driver.find_element_by_name("foreseenuseinfotype_model_set-0-foreseenUse")).select_by_visible_text(
      "Human Use")
    Select(driver.find_element_by_name(
      "foreseenuseinfotype_model_set-0-useNLPSpecific_old")).select_by_visible_text("Annotation")
    driver.find_element_by_xpath(
      "//div[@id='foreseenuseinfotype_model_set-0']/fieldset/div[@class='form-row useNLPSpecific']/div/div/ul/li/a") \
      .click()
    
    # actual uses
    driver.find_element_by_id("fieldsetcollapser1").click()
    Select(driver.find_element_by_name("actualuseinfotype_model_set-0-actualUse")).select_by_visible_text(
      "Human Use")
    Select(driver.find_element_by_name(
      "actualuseinfotype_model_set-0-useNLPSpecific_old")).select_by_visible_text("Annotation")
    driver.find_element_by_xpath(
      "//div[@id='actualuseinfotype_model_set-0']/fieldset/div[@class='form-row useNLPSpecific']/div/div/ul/li/a") \
      .click()
    Select(driver.find_element_by_name("subclass_select")).select_by_visible_text("documentInfoType")
    _fill_usage_report(driver, ss_path, current_id)
    driver.find_element_by_xpath("//a[@id='add_id_actualuseinfotype_model_set-0-derivedResource']/img").click()  
    _fill_derived_resource(driver, ss_path, current_id)
    driver.find_element_by_xpath("//a[@id='add_id_actualuseinfotype_model_set-0-usageProject']/img").click()  
    _fill_project(driver, ss_path, current_id)
    driver.find_element_by_name("actualuseinfotype_model_set-0-actualUseDetails").clear()
    driver.find_element_by_name("actualuseinfotype_model_set-0-actualUseDetails").send_keys("details")
    
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_access_tool(driver, ss_path, parent_id):
    """
    fills the access tool popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_accessTool")
    driver.find_element_by_name("targetResourceNameURI").clear()
    driver.find_element_by_name("targetResourceNameURI").send_keys("578DFDG8DF")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_resource_associated_with(driver, ss_path, parent_id):
    """
    fills the resource associated with popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_resourceAssociatedWith")
    driver.find_element_by_name("targetResourceNameURI").clear()
    driver.find_element_by_name("targetResourceNameURI").send_keys("578DFDG8DF")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_usage_report(driver, ss_path, parent_id):
    """
    fills the usage report popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_actualuseinfotype_model_set__dash__0__dash__usageReport")
    Select(driver.find_element_by_id("id_documentType")).select_by_visible_text("Article")
    driver.find_element_by_name("key_title_0").clear()
    driver.find_element_by_name("key_title_0").send_keys("en")
    driver.find_element_by_name("val_title_0").clear()
    driver.find_element_by_name("val_title_0").send_keys("Document title")
    driver.find_element_by_name("author").clear()
    driver.find_element_by_name("author").send_keys("John Smith")
    driver.find_element_by_name("editor").clear()
    driver.find_element_by_name("editor").send_keys("Smith Ed.")
    driver.find_element_by_name("year").clear()
    driver.find_element_by_name("year").send_keys("1981")
    driver.find_element_by_name("publisher").clear()
    driver.find_element_by_name("publisher").send_keys("John Smith & Co")
    driver.find_element_by_name("bookTitle").clear()
    driver.find_element_by_name("bookTitle").send_keys("Life of John Smith")
    driver.find_element_by_name("journal").clear()
    driver.find_element_by_name("journal").send_keys("Journal")
    driver.find_element_by_name("volume").clear()
    driver.find_element_by_name("volume").send_keys("7")
    driver.find_element_by_name("series").clear()
    driver.find_element_by_name("series").send_keys("9")
    driver.find_element_by_name("pages").clear()
    driver.find_element_by_name("pages").send_keys("289-290")
    driver.find_element_by_name("edition").clear()
    driver.find_element_by_name("edition").send_keys("1st")
    driver.find_element_by_name("conference").clear()
    driver.find_element_by_name("conference").send_keys("Main conference")
    driver.find_element_by_name("doi").clear()
    driver.find_element_by_name("doi").send_keys("123-35-1243")
    driver.find_element_by_name("url").clear()
    driver.find_element_by_name("url").send_keys("http://www.mainconference.org")
    driver.find_element_by_name("ISSN").clear()
    driver.find_element_by_name("ISSN").send_keys("12-435-464-467")
    driver.find_element_by_name("ISBN").clear()
    driver.find_element_by_name("ISBN").send_keys("12-435-464-467")
    driver.find_element_by_name("keywords").clear()
    driver.find_element_by_name("keywords").send_keys("John Smith, life")
    driver.find_element_by_name("documentLanguageName").clear()
    driver.find_element_by_name("documentLanguageName").send_keys("English")
    driver.find_element_by_name("documentLanguageId").clear()
    driver.find_element_by_name("documentLanguageId").send_keys("en")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_documentation(driver, ss_path, parent_id):
    """
    fills the documentation popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_form__dash__4__dash__0__dash__documentation")
    Select(driver.find_element_by_id("id_documentType")).select_by_visible_text("Article")
    driver.find_element_by_name("key_title_0").clear()
    driver.find_element_by_name("key_title_0").send_keys("en")
    driver.find_element_by_name("val_title_0").clear()
    driver.find_element_by_name("val_title_0").send_keys("Document title")
    driver.find_element_by_name("author").clear()
    driver.find_element_by_name("author").send_keys("John Smith")
    driver.find_element_by_name("editor").clear()
    driver.find_element_by_name("editor").send_keys("Smith Ed.")
    driver.find_element_by_name("year").clear()
    driver.find_element_by_name("year").send_keys("1981")
    driver.find_element_by_name("publisher").clear()
    driver.find_element_by_name("publisher").send_keys("John Smith & Co")
    driver.find_element_by_name("bookTitle").clear()
    driver.find_element_by_name("bookTitle").send_keys("Life of John Smith")
    driver.find_element_by_name("journal").clear()
    driver.find_element_by_name("journal").send_keys("Journal")
    driver.find_element_by_name("volume").clear()
    driver.find_element_by_name("volume").send_keys("7")
    driver.find_element_by_name("series").clear()
    driver.find_element_by_name("series").send_keys("9")
    driver.find_element_by_name("pages").clear()
    driver.find_element_by_name("pages").send_keys("289-290")
    driver.find_element_by_name("edition").clear()
    driver.find_element_by_name("edition").send_keys("1st")
    driver.find_element_by_name("conference").clear()
    driver.find_element_by_name("conference").send_keys("Main conference")
    driver.find_element_by_name("doi").clear()
    driver.find_element_by_name("doi").send_keys("123-35-1243")
    driver.find_element_by_name("url").clear()
    driver.find_element_by_name("url").send_keys("http://www.mainconference.org")
    driver.find_element_by_name("ISSN").clear()
    driver.find_element_by_name("ISSN").send_keys("12-435-464-467")
    driver.find_element_by_name("ISBN").clear()
    driver.find_element_by_name("ISBN").send_keys("12-435-464-467")
    driver.find_element_by_name("keywords").clear()
    driver.find_element_by_name("keywords").send_keys("John Smith, life")
    driver.find_element_by_name("documentLanguageName").clear()
    driver.find_element_by_name("documentLanguageName").send_keys("English")
    driver.find_element_by_name("documentLanguageId").clear()
    driver.find_element_by_name("documentLanguageId").send_keys("en")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_derived_resource(driver, ss_path, parent_id):
    """
    fills the derived resource popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_actualuseinfotype_model_set__dash__0__dash__derivedResource")
    driver.find_element_by_name("targetResourceNameURI").clear()
    driver.find_element_by_name("targetResourceNameURI").send_keys("578DFDG8DF")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_related_resource(driver, ss_path, parent_id):
    """
    fills the related resource popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_relationinfotype_model_set__dash__0__dash__relatedResource")
    driver.find_element_by_name("targetResourceNameURI").clear()
    driver.find_element_by_name("targetResourceNameURI").send_keys("578DFDG8DF")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_project(driver, ss_path, parent_id):
    """
    fills the project popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_actualuseinfotype_model_set__dash__0__dash__usageProject")
    driver.find_element_by_name("key_projectName_0").clear()
    driver.find_element_by_name("key_projectName_0").send_keys("en")
    driver.find_element_by_name("val_projectName_0").clear()
    driver.find_element_by_name("val_projectName_0").send_keys("Project")
    driver.find_element_by_xpath("//div[@class='form-row projectShortName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_projectShortName_0").clear()
    driver.find_element_by_name("key_projectShortName_0").send_keys("en")
    driver.find_element_by_name("val_projectShortName_0").clear()
    driver.find_element_by_name("val_projectShortName_0").send_keys("Short name")
    driver.find_element_by_name("projectID").clear()
    driver.find_element_by_name("projectID").send_keys("A-123")
    driver.find_element_by_name("url").clear()
    driver.find_element_by_name("url").send_keys("http://www.project.org")
    Select(driver.find_element_by_name("fundingType_old")).select_by_visible_text("Other")
    driver.find_element_by_xpath("//a[@class='selector-add']").click()
    driver.find_element_by_name("funder").clear()
    driver.find_element_by_name("funder").send_keys("Funder of the project")
    driver.find_element_by_name("fundingCountry").clear()
    driver.find_element_by_name("fundingCountry").send_keys("world")
    driver.find_element_by_name("projectStartDate").clear()
    driver.find_element_by_name("projectStartDate").send_keys("2012-09-27")
    driver.find_element_by_name("projectEndDate").clear()
    driver.find_element_by_name("projectEndDate").send_keys("2012-09-27")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_funding_project(driver, ss_path, parent_id):
    """
    fills the funding project popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_form__dash__5__dash__0__dash__fundingProject")
    driver.find_element_by_name("key_projectName_0").clear()
    driver.find_element_by_name("key_projectName_0").send_keys("en")
    driver.find_element_by_name("val_projectName_0").clear()
    driver.find_element_by_name("val_projectName_0").send_keys("Project")
    driver.find_element_by_xpath("//div[@class='form-row projectShortName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_projectShortName_0").clear()
    driver.find_element_by_name("key_projectShortName_0").send_keys("en")
    driver.find_element_by_name("val_projectShortName_0").clear()
    driver.find_element_by_name("val_projectShortName_0").send_keys("Short name")
    driver.find_element_by_name("projectID").clear()
    driver.find_element_by_name("projectID").send_keys("A-123")
    driver.find_element_by_name("url").clear()
    driver.find_element_by_name("url").send_keys("http://www.project.org")
    Select(driver.find_element_by_name("fundingType_old")).select_by_visible_text("Other")
    driver.find_element_by_xpath("//a[@class='selector-add']").click()
    driver.find_element_by_name("funder").clear()
    driver.find_element_by_name("funder").send_keys("Funder of the project")
    driver.find_element_by_name("fundingCountry").clear()
    driver.find_element_by_name("fundingCountry").send_keys("world")
    driver.find_element_by_name("projectStartDate").clear()
    driver.find_element_by_name("projectStartDate").send_keys("2012-09-27")
    driver.find_element_by_name("projectEndDate").clear()
    driver.find_element_by_name("projectEndDate").send_keys("2012-09-27")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_metadata_creator(driver, ss_path, parent_id):
    """
    fills the metadata creator popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_form__dash__2__dash__0__dash__metadataCreator")
    current_id = driver.current_window_handle
    driver.find_element_by_name("key_surname_0").clear()
    driver.find_element_by_name("key_surname_0").send_keys("en")
    driver.find_element_by_name("val_surname_0").clear()
    driver.find_element_by_name("val_surname_0").send_keys("Smith")
    driver.find_element_by_xpath("//div[@class='form-row givenName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_givenName_0").clear()
    driver.find_element_by_name("key_givenName_0").send_keys("en")
    driver.find_element_by_name("val_givenName_0").clear()
    driver.find_element_by_name("val_givenName_0").send_keys("John")
    Select(driver.find_element_by_id("id_sex")).select_by_visible_text("Male")

    driver.find_element_by_name("form-0-email").clear()
    driver.find_element_by_name("form-0-email").send_keys("john.smith@institution.org")
    driver.find_element_by_name("form-0-url").clear()
    driver.find_element_by_name("form-0-url").send_keys("http://www.institution.org")
    driver.find_element_by_name("form-0-address").clear()
    driver.find_element_by_name("form-0-address").send_keys("1st main street")
    driver.find_element_by_name("form-0-zipCode").clear()
    driver.find_element_by_name("form-0-zipCode").send_keys("95000")
    driver.find_element_by_name("form-0-city").clear()
    driver.find_element_by_name("form-0-city").send_keys("somewhere")
    driver.find_element_by_name("form-0-region").clear()
    driver.find_element_by_name("form-0-region").send_keys("far away")
    driver.find_element_by_name("form-0-country").clear()
    driver.find_element_by_name("form-0-country").send_keys("world")
    driver.find_element_by_name("form-0-telephoneNumber").clear()
    driver.find_element_by_name("form-0-telephoneNumber").send_keys("1234567890")
    driver.find_element_by_name("form-0-faxNumber").clear()
    driver.find_element_by_name("form-0-faxNumber").send_keys("1234567890")
    driver.find_element_by_name("position").clear()
    driver.find_element_by_name("position").send_keys("Organization")
    # affiliation popup
    driver.find_element_by_xpath("//a[@id='add_id_affiliation']/img").click()
    _fill_affiliation(driver, ss_path, current_id)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_resource_creator(driver, ss_path, parent_id):
    """
    fills the resource creator popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_form__dash__5__dash__0__dash__resourceCreator")
    current_id = driver.current_window_handle
    driver.find_element_by_name("key_surname_0").clear()
    driver.find_element_by_name("key_surname_0").send_keys("en")
    driver.find_element_by_name("val_surname_0").clear()
    driver.find_element_by_name("val_surname_0").send_keys("Smith")
    driver.find_element_by_xpath("//div[@class='form-row givenName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_givenName_0").clear()
    driver.find_element_by_name("key_givenName_0").send_keys("en")
    driver.find_element_by_name("val_givenName_0").clear()
    driver.find_element_by_name("val_givenName_0").send_keys("John")
    Select(driver.find_element_by_id("id_sex")).select_by_visible_text("Male")

    driver.find_element_by_name("form-0-email").clear()
    driver.find_element_by_name("form-0-email").send_keys("john.smith@institution.org")
    driver.find_element_by_name("form-0-url").clear()
    driver.find_element_by_name("form-0-url").send_keys("http://www.institution.org")
    driver.find_element_by_name("form-0-address").clear()
    driver.find_element_by_name("form-0-address").send_keys("1st main street")
    driver.find_element_by_name("form-0-zipCode").clear()
    driver.find_element_by_name("form-0-zipCode").send_keys("95000")
    driver.find_element_by_name("form-0-city").clear()
    driver.find_element_by_name("form-0-city").send_keys("somewhere")
    driver.find_element_by_name("form-0-region").clear()
    driver.find_element_by_name("form-0-region").send_keys("far away")
    driver.find_element_by_name("form-0-country").clear()
    driver.find_element_by_name("form-0-country").send_keys("world")
    driver.find_element_by_name("form-0-telephoneNumber").clear()
    driver.find_element_by_name("form-0-telephoneNumber").send_keys("1234567890")
    driver.find_element_by_name("form-0-faxNumber").clear()
    driver.find_element_by_name("form-0-faxNumber").send_keys("1234567890")
    driver.find_element_by_name("position").clear()
    driver.find_element_by_name("position").send_keys("Organization")
    # affiliation popup
    driver.find_element_by_xpath("//a[@id='add_id_affiliation']/img").click()
    _fill_affiliation(driver, ss_path, current_id)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_ipr_holder(driver, ss_path, parent_id):
    """
    fills the ipr holder popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_iprHolder")
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("key_surname_0").clear()
    driver.find_element_by_name("key_surname_0").send_keys("en")
    driver.find_element_by_name("val_surname_0").clear()
    driver.find_element_by_name("val_surname_0").send_keys("Smith")
    driver.find_element_by_xpath("//div[@class='form-row givenName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_givenName_0").clear()
    driver.find_element_by_name("key_givenName_0").send_keys("en")
    driver.find_element_by_name("val_givenName_0").clear()
    driver.find_element_by_name("val_givenName_0").send_keys("John")
    Select(driver.find_element_by_id("id_sex")).select_by_visible_text("Male")
    driver.find_element_by_name("form-0-email").clear()
    driver.find_element_by_name("form-0-email").send_keys("john.smith@institution.org")
    driver.find_element_by_name("form-0-url").clear()
    driver.find_element_by_name("form-0-url").send_keys("http://www.institution.org")
    driver.find_element_by_name("form-0-address").clear()
    driver.find_element_by_name("form-0-address").send_keys("1st main street")
    driver.find_element_by_name("form-0-zipCode").clear()
    driver.find_element_by_name("form-0-zipCode").send_keys("95000")
    driver.find_element_by_name("form-0-city").clear()
    driver.find_element_by_name("form-0-city").send_keys("somewhere")
    driver.find_element_by_name("form-0-region").clear()
    driver.find_element_by_name("form-0-region").send_keys("far away")
    driver.find_element_by_name("form-0-country").clear()
    driver.find_element_by_name("form-0-country").send_keys("world")
    driver.find_element_by_name("form-0-telephoneNumber").clear()
    driver.find_element_by_name("form-0-telephoneNumber").send_keys("1234567890")
    driver.find_element_by_name("form-0-faxNumber").clear()
    driver.find_element_by_name("form-0-faxNumber").send_keys("1234567890")
    driver.find_element_by_name("position").clear()
    driver.find_element_by_name("position").send_keys("Professor")
    # affiliation popup
    driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
    _fill_affiliation(driver, ss_path, current_id)
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_licensor(driver, ss_path, parent_id):
    """
    fills the licensor popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_licenceinfotype_model_set__dash__0__dash__licensor")
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("key_surname_0").clear()
    driver.find_element_by_name("key_surname_0").send_keys("en")
    driver.find_element_by_name("val_surname_0").clear()
    driver.find_element_by_name("val_surname_0").send_keys("Smith")
    driver.find_element_by_xpath("//div[@class='form-row givenName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_givenName_0").clear()
    driver.find_element_by_name("key_givenName_0").send_keys("en")
    driver.find_element_by_name("val_givenName_0").clear()
    driver.find_element_by_name("val_givenName_0").send_keys("John")
    Select(driver.find_element_by_id("id_sex")).select_by_visible_text("Male")
    driver.find_element_by_name("form-0-email").clear()
    driver.find_element_by_name("form-0-email").send_keys("john.smith@institution.org")
    driver.find_element_by_name("form-0-url").clear()
    driver.find_element_by_name("form-0-url").send_keys("http://www.institution.org")
    driver.find_element_by_name("form-0-address").clear()
    driver.find_element_by_name("form-0-address").send_keys("1st main street")
    driver.find_element_by_name("form-0-zipCode").clear()
    driver.find_element_by_name("form-0-zipCode").send_keys("95000")
    driver.find_element_by_name("form-0-city").clear()
    driver.find_element_by_name("form-0-city").send_keys("somewhere")
    driver.find_element_by_name("form-0-region").clear()
    driver.find_element_by_name("form-0-region").send_keys("far away")
    driver.find_element_by_name("form-0-country").clear()
    driver.find_element_by_name("form-0-country").send_keys("world")
    driver.find_element_by_name("form-0-telephoneNumber").clear()
    driver.find_element_by_name("form-0-telephoneNumber").send_keys("1234567890")
    driver.find_element_by_name("form-0-faxNumber").clear()
    driver.find_element_by_name("form-0-faxNumber").send_keys("1234567890")
    driver.find_element_by_name("position").clear()
    driver.find_element_by_name("position").send_keys("Professor")
    # affiliation popup
    driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
    _fill_affiliation(driver, ss_path, current_id)
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_distribution_rights_holder(driver, ss_path, parent_id):
    """
    fills the distributino rights holder popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_licenceinfotype_model_set__dash__0__dash__distributionRightsHolder")
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("key_surname_0").clear()
    driver.find_element_by_name("key_surname_0").send_keys("en")
    driver.find_element_by_name("val_surname_0").clear()
    driver.find_element_by_name("val_surname_0").send_keys("Smith")
    driver.find_element_by_xpath("//div[@class='form-row givenName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_givenName_0").clear()
    driver.find_element_by_name("key_givenName_0").send_keys("en")
    driver.find_element_by_name("val_givenName_0").clear()
    driver.find_element_by_name("val_givenName_0").send_keys("John")
    Select(driver.find_element_by_id("id_sex")).select_by_visible_text("Male")
    driver.find_element_by_name("form-0-email").clear()
    driver.find_element_by_name("form-0-email").send_keys("john.smith@institution.org")
    driver.find_element_by_name("form-0-url").clear()
    driver.find_element_by_name("form-0-url").send_keys("http://www.institution.org")
    driver.find_element_by_name("form-0-address").clear()
    driver.find_element_by_name("form-0-address").send_keys("1st main street")
    driver.find_element_by_name("form-0-zipCode").clear()
    driver.find_element_by_name("form-0-zipCode").send_keys("95000")
    driver.find_element_by_name("form-0-city").clear()
    driver.find_element_by_name("form-0-city").send_keys("somewhere")
    driver.find_element_by_name("form-0-region").clear()
    driver.find_element_by_name("form-0-region").send_keys("far away")
    driver.find_element_by_name("form-0-country").clear()
    driver.find_element_by_name("form-0-country").send_keys("world")
    driver.find_element_by_name("form-0-telephoneNumber").clear()
    driver.find_element_by_name("form-0-telephoneNumber").send_keys("1234567890")
    driver.find_element_by_name("form-0-faxNumber").clear()
    driver.find_element_by_name("form-0-faxNumber").send_keys("1234567890")
    driver.find_element_by_name("position").clear()
    driver.find_element_by_name("position").send_keys("Professor")
    # affiliation popup
    driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
    _fill_affiliation(driver, ss_path, current_id)
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_membership(driver, ss_path, parent_id):
    """
    fills the membership popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("id_licenceinfotype_model_set__dash__0__dash__membershipInfo")
    Select(driver.find_element_by_xpath("//div[@class='form-row member']/div/select")).select_by_visible_text("Yes")
    Select(driver.find_element_by_name(
      "membershipInstitution_old")).select_by_visible_text("LDC")
    driver.find_element_by_xpath(
      "//div[@class='form-row membershipInstitution']/div/div/ul/li/a") \
      .click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_language(driver, ss_path, id_infix):
    """
    fills the language with required, recommended and optional information
    """
    driver.find_element_by_id("id_{}languageId".format(id_infix)).clear()
    driver.find_element_by_id("id_{}languageId".format(id_infix)).send_keys("De")
    driver.find_element_by_id("id_{}languageName".format(id_infix)).clear()
    driver.find_element_by_id("id_{}languageName".format(id_infix)).send_keys("German")
    driver.find_element_by_id("id_{}languageScript".format(id_infix)).clear()
    driver.find_element_by_id("id_{}languageScript".format(id_infix)).send_keys("Script")


def _fill_size_per_language(driver, ss_path, id_infix):
    """
    fills the size per language popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to_window("add_id_languageinfotype_model_set__dash__0__dash__sizePerLanguage")
    driver.find_element_by_id("id_size".format(id_infix)).clear()
    driver.find_element_by_id("id_size".format(id_infix)).send_keys("12")
    Select(driver.find_element_by_xpath("//div[@class='form-row sizeUnit']/div/select")).select_by_visible_text("Classes")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_text_size(driver, ss_path, id_infix):
    """
    fills the text size with required information
    """
    driver.find_element_by_id("id_{}size".format(id_infix)).clear()
    driver.find_element_by_id("id_{}size".format(id_infix)).send_keys("10000")
    Select(driver.find_element_by_id("id_{}sizeUnit".format(id_infix))).select_by_visible_text("Tokens")


def _fill_audio_size(driver, ss_path, parent_id):
    """
    fills the text size with required information
    """
    driver.switch_to_window("id_audioSizeInfo")
    driver.find_element_by_id("id_sizeinfotype_model_set-0-size").send_keys("100")
    Select(driver.find_element_by_id("id_sizeinfotype_model_set-0-sizeUnit")).select_by_visible_text("Gb")
    save_and_close(driver, parent_id) 


def _ingest(driver):
    """
    selects all resources and ingests them
    """
    driver.find_element_by_id("action-toggle").click()
    Select(driver.find_element_by_name("action")) \
        .select_by_visible_text("Ingest selected internal resources")
    driver.find_element_by_name("index").click()
    # TODO remove this workaround when Selenium starts working again as intended
    time.sleep(1)


def _publish(driver):
    """
    selects all resources and publishes them
    """
    driver.find_element_by_id("action-toggle").click()
    Select(driver.find_element_by_name("action")) \
        .select_by_visible_text("Publish selected ingested resources")
    driver.find_element_by_name("index").click()
    # TODO remove this workaround when Selenium starts working again as intended
    time.sleep(1)


def _delete(driver):
    """
    selects all resources and deletes them
    """
    driver.find_element_by_id("action-toggle").click()
    Select(driver.find_element_by_name("action")) \
        .select_by_visible_text("Mark selected resources as deleted")
    driver.find_element_by_name("index").click()
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    # TODO remove this workaround when Selenium starts working again as intended
    time.sleep(1)
