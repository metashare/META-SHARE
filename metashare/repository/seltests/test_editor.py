import time

from django.core.management import call_command

from selenium.webdriver.support.ui import Select

from metashare import settings, test_utils
from metashare.accounts.models import EditorGroup, EditorGroupManagers
from metashare.repository.models import resourceInfoType_model
from metashare.repository.seltests.test_utils import login_user, mouse_over, \
    setup_screenshots_folder, click_menu_item, save_and_close, \
    cancel_and_close, MetashareSeleniumTestCase
from metashare.settings import DJANGO_URL, DJANGO_BASE, ROOT_PATH


TESTFIXTURE_XML = '{}/repository/fixtures/ILSP10.xml'.format(ROOT_PATH)

class BasicEditorTests(MetashareSeleniumTestCase):
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
        self.base_url = '{0}/{1}'.format(DJANGO_URL, DJANGO_BASE)
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
        driver.implicitly_wait(60) # wait for 60 seconds
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
        driver.implicitly_wait(60) # wait for 60 seconds
        driver.get(self.base_url)
        self.spin_assert(lambda: self.assertEqual(driver.title, "META-SHARE"))
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.EditorTest",
          "LR_creation_tool")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))  
        # login user
        login_user(driver, "manageruser", "secret")
        # make sure login was successful
        self.assertEqual("Logout", 
          driver.find_element_by_xpath("//div[@id='inner']/div[2]/a/div").text)
        self.spin_assert(lambda: self.assertEqual(driver.title, "META-SHARE"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Manage Resources -> Manage all resources
        mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
        self.spin_assert(lambda: self.assertTrue(driver.title.startswith("Select Resource to change")))
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # Add resource
        driver.find_element_by_link_text("Add Resource").click()
        self.spin_assert(lambda: driver.title.startswith("Add Resource"))
        # create tool
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(
          "Tool / Service")
        driver.find_element_by_id("id_submit").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.spin_assert(lambda: self.assertEqual("Add Resource", 
          driver.find_element_by_css_selector("#content > h1").text))
        # remember root window id
        root_id = driver.current_window_handle
        # add required fields
        # (add an invalid character in the resource name to verify that invalid
        # characters are found in DictField values)
        driver.find_element_by_name("key_form-0-resourceName_0").click()
        driver.find_element_by_name("key_form-0-resourceName_0").clear()
        driver.find_element_by_name("key_form-0-resourceName_0").send_keys("en")
        #self.spin_assert(lambda: self.assertEqual("en",
        #      driver.find_element_by_name("key_form-0-resourceName_0").text))
        driver.find_element_by_name("val_form-0-resourceName_0").click()
        driver.find_element_by_name("val_form-0-resourceName_0").clear()
        driver.find_element_by_name("val_form-0-resourceName_0").send_keys(u"Test\u000b Tool")
        driver.find_element_by_name("key_form-0-description_0").clear()
        driver.find_element_by_name("key_form-0-description_0").send_keys("en")
        driver.find_element_by_name("val_form-0-description_0").clear()
        driver.find_element_by_name("val_form-0-description_0").send_keys("Test Description")
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # distribution popup
        driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()
        _fill_distribution_popup(self, driver, ss_path, root_id)
        # contact person popup
        driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
        _fill_contactPerson_popup(self, driver, ss_path, root_id)

        # tool info popup
        driver.find_element_by_id("edit_id_toolServiceInfo").click()
        driver.switch_to.window("edit_id_toolServiceInfo")
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
        driver.implicitly_wait(60) # wait for 60 seconds
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
        driver.switch_to.window("id_distributionInfo")
        # check sorting of Availability
        self.assertEqual("Available - Restricted Use", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[2]").text)
        self.assertEqual("Available - Unrestricted Use", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[3]").text)
        self.assertEqual("Not Available Through Meta Share", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[4]").text)
        self.assertEqual("Under Negotiation", driver.find_element_by_xpath(
          "//select[@id='id_availability']/option[5]").text)
        cancel_and_close(driver, root_id)
        # corpus info text popup
        driver.find_element_by_id("add_id_corpusTextInfo-0").click()
        driver.switch_to.window("id_corpusTextInfo__dash__0")
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
        driver.implicitly_wait(60) # wait for 60 seconds
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
        driver.switch_to.window("id_distributionInfo")
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


def _add_new_resource(driver, ss_path, resource_type, media_types):
    """
    adds a new resource with specific resource type and media types
    """
    # Manage Resources -> Manage all resources
    mouse_over(driver, driver.find_element_by_link_text("Manage Resources"))
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    click_menu_item(driver, driver.find_element_by_link_text("Manage all resources"))
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    # Add resource
    driver.find_element_by_link_text("Add Resource").click()
    #Select resource type
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    Select(driver.find_element_by_id("id_resourceType")).select_by_visible_text(resource_type)
    for media_type in media_types:
        driver.find_element_by_id(media_type).click()
    driver.find_element_by_id("id_submit").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))


def _fill_administrativeInformation_forms(test, driver, ss_path, root_id):
    """
    fills the different administrative information forms with required,
    recommended and optional information
    """
    # identification fields
    _fill_identification_form(driver, ss_path, "form-0-")
    # distribution popup
    driver.find_element_by_css_selector("img[alt=\"Add information\"]").click()  
    _fill_distribution_popup(test, driver, ss_path, root_id)
    # contact person popup
    driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
    _fill_contactPerson_popup(test, driver, ss_path, root_id)
    # metadata fields
    _fill_metadata_form(test, driver, ss_path, "form-2-0-")

    # recommended page
    driver.find_element_by_css_selector("a[href=\"#field-2\"]").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    # version fields
    _fill_version_form(driver, ss_path, "form-3-0-")
    # validations fields
    driver.find_element_by_id("fieldsetcollapser0").click()
    _fill_validations_form(test, driver, ss_path, "validationinfotype_model_set-0-")
    # usage popup
    driver.find_element_by_xpath("//a[@id='add_id_usageInfo']/img").click()  
    _fill_usage_popup(driver, ss_path, root_id)
    # resource documentation fields 
    _fill_resourceDocumentation_form(driver, ss_path, "form-4-0-")
    # resource creation fields 
    _fill_resourceCreation_form(test, driver, ss_path, "form-5-0-")
    # relations fields
    driver.find_element_by_id("fieldsetcollapser1").click()
    _fill_relations_form(driver, ss_path, "relationinfotype_model_set-0-")


def _fill_identification_form(driver, ss_path, id_infix):
    """
    fills the identification form with required, recommended and optional information
    """
    driver.find_element_by_name("key_{}resourceName_0".format(id_infix)).clear()
    driver.find_element_by_name("key_{}resourceName_0".format(id_infix)).send_keys("en")
    driver.find_element_by_name("val_{}resourceName_0".format(id_infix)).clear()
    driver.find_element_by_name("val_{}resourceName_0".format(id_infix)).send_keys("Resource Name")
    driver.find_element_by_name("key_{}description_0".format(id_infix)).clear()
    driver.find_element_by_name("key_{}description_0".format(id_infix)).send_keys("en")
    driver.find_element_by_name("val_{}description_0".format(id_infix)).clear()
    driver.find_element_by_name("val_{}description_0".format(id_infix)).send_keys("Test Description")
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_xpath("//div[@class='form-row resourceShortName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_{}resourceShortName_0".format(id_infix)).clear()
    driver.find_element_by_name("key_{}resourceShortName_0".format(id_infix)).send_keys("en")
    driver.find_element_by_name("val_{}resourceShortName_0".format(id_infix)).clear()
    driver.find_element_by_name("val_{}resourceShortName_0".format(id_infix)).send_keys("RN")
    driver.find_element_by_name("{}url".format(id_infix)).clear()
    driver.find_element_by_name("{}url".format(id_infix)).send_keys("http://www.rn.org")
    driver.find_element_by_name("{}identifier".format(id_infix)).clear()
    driver.find_element_by_name("{}identifier".format(id_infix)).send_keys("A-123")


def _fill_metadata_form(test, driver, ss_path, id_infix):
    """
    fills the metadata form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    # contact metadata creator popup
    driver.find_element_by_xpath("//a[@id='add_id_{}metadataCreator']/img".format(id_infix)).click()
    _fill_metadataCreator_popup(test, driver, ss_path, current_id)
    driver.find_element_by_name("{}source".format(id_infix)).clear()
    driver.find_element_by_name("{}source".format(id_infix)).send_keys("catalogue")
    driver.find_element_by_name("{}originalMetadataSchema".format(id_infix)).clear()
    driver.find_element_by_name("{}originalMetadataSchema".format(id_infix)).send_keys("metadata")
    driver.find_element_by_name("{}originalMetadataLink".format(id_infix)).clear()
    driver.find_element_by_name("{}originalMetadataLink".format(id_infix)).send_keys("http://catalogue.org/rn")
    driver.find_element_by_name("{}metadataLanguageName".format(id_infix)).clear()
    driver.find_element_by_name("{}metadataLanguageName".format(id_infix)).send_keys("english")
    driver.find_element_by_name("{}metadataLanguageId".format(id_infix)).clear()
    driver.find_element_by_name("{}metadataLanguageId".format(id_infix)).send_keys("en")
    driver.find_element_by_name("{}revision".format(id_infix)).clear()
    driver.find_element_by_name("{}revision".format(id_infix)).send_keys("1.0")


def _fill_version_form(driver, ss_path, id_infix):
    """
    fills the version form with required, recommended and optional information
    """
    driver.find_element_by_name("{}version".format(id_infix)).clear()
    driver.find_element_by_name("{}version".format(id_infix)).send_keys("1.0")
    driver.find_element_by_name("{}revision".format(id_infix)).clear()
    driver.find_element_by_name("{}revision".format(id_infix)).send_keys("1.0")
    driver.find_element_by_name("{}lastDateUpdated".format(id_infix)).clear()
    driver.find_element_by_name("{}lastDateUpdated".format(id_infix)).send_keys("2012-09-28")
    driver.find_element_by_name("{}updateFrequency".format(id_infix)).clear()
    driver.find_element_by_name("{}updateFrequency".format(id_infix)).send_keys("1")


def _fill_modalities_form(driver, ss_path, id_infix):
    """
    fills the modalities form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    Select(driver.find_element_by_name(
      "{}modalityType_old".format(id_infix))).select_by_visible_text("Voice")
    driver.find_element_by_xpath("//td[@class='modalityType']/span/div/ul/li/a").click()
    driver.find_element_by_name("{}modalityTypeDetails".format(id_infix)).clear()
    driver.find_element_by_name("{}modalityTypeDetails".format(id_infix)).send_keys("Details")
    # size per modalities popup
    driver.find_element_by_xpath("//a[@id='add_id_{}sizePerModality']/img".format(id_infix)).click()  
    _fill_sizePerModalities_popup(driver, ss_path, current_id)


def _fill_textFormats_form(driver, ss_path, id_infix):
    """
    fills the text formats form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("{}mimeType".format(id_infix)).clear()
    driver.find_element_by_name("{}mimeType".format(id_infix)).send_keys("application/pdf")
    # size per text format popup
    driver.find_element_by_xpath("//a[@id='add_id_{}sizePerTextFormat']/img".format(id_infix)).click()  
    _fill_sizePerTextFormats_popup(driver, ss_path, current_id)


def _fill_characterEncodings_form(driver, ss_path, id_infix):
    """
    fills the character encodings form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    Select(driver.find_element_by_name(
      "{}characterEncoding".format(id_infix))).select_by_visible_text("Cp1097")
    # size per character encodings popup
    driver.find_element_by_xpath("//a[@id='add_id_{}sizePerCharacterEncoding']/img".format(id_infix)) \
      .click()  
    _fill_sizePerCharacterEncodings_popup(driver, ss_path, current_id)


def _fill_annotations_form(test, driver, ss_path, id_infix):
    """
    fills the annotations form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    Select(driver.find_element_by_name(
      "{}annotationType".format(id_infix))).select_by_visible_text("Alignment")
    Select(driver.find_element_by_name(
      "{}annotatedElements_old".format(id_infix))).select_by_visible_text("Truncation")
    driver.find_element_by_xpath("//div[@class='form-row annotatedElements']/div/div/div/a") \
      .click()
    Select(driver.find_element_by_name(
      "{}annotationStandoff".format(id_infix))).select_by_visible_text("Yes")
    Select(driver.find_element_by_name(
      "{}segmentationLevel_old".format(id_infix))).select_by_visible_text("Phoneme")
    driver.find_element_by_xpath("//div[@class='form-row segmentationLevel']/div/div/div/a") \
      .click()
    driver.find_element_by_name("{}annotationFormat".format(id_infix)).clear()
    driver.find_element_by_name("{}annotationFormat".format(id_infix)).send_keys("Format")
    driver.find_element_by_name("{}tagset".format(id_infix)).clear()
    driver.find_element_by_name("{}tagset".format(id_infix)).send_keys("tagset")
    driver.find_element_by_name("{}tagsetLanguageId".format(id_infix)).clear()
    driver.find_element_by_name("{}tagsetLanguageId".format(id_infix)).send_keys("En")
    driver.find_element_by_name("{}tagsetLanguageName".format(id_infix)).clear()
    driver.find_element_by_name("{}tagsetLanguageName".format(id_infix)).send_keys("English")
    Select(driver.find_element_by_name(
      "{}conformanceToStandardsBestPractices_old".format(id_infix))).select_by_visible_text("EMMA")
    driver.find_element_by_xpath(
      "//div[@class='form-row conformanceToStandardsBestPractices']/div/div/div/a").click()
    driver.find_element_by_name("{}theoreticModel".format(id_infix)).clear()
    driver.find_element_by_name("{}theoreticModel".format(id_infix)).send_keys("Model")
    # annotation manual popup
    Select(driver.find_element_by_xpath("//div[@class='form-row annotationManual']/div/select")) \
      .select_by_visible_text("documentInfoType")
    _fill_annotationManual_popup(driver, ss_path, current_id)
    Select(driver.find_element_by_name(
      "{}annotationMode".format(id_infix))).select_by_visible_text("Automatic")
    driver.find_element_by_name("{}annotationModeDetails".format(id_infix)).clear()
    driver.find_element_by_name("{}annotationModeDetails".format(id_infix)).send_keys("Details")
    # annotation tool popup
    driver.find_element_by_xpath("//a[@id='add_id_{}annotationTool']/img".format(id_infix)) \
      .click()  
    _fill_annotationTool_popup(driver, ss_path, current_id)
    driver.find_element_by_name("{}annotationStartDate".format(id_infix)).clear()
    driver.find_element_by_name("{}annotationStartDate".format(id_infix)).send_keys("2012-10-04")
    driver.find_element_by_name("{}annotationEndDate".format(id_infix)).clear()
    driver.find_element_by_name("{}annotationEndDate".format(id_infix)).send_keys("2012-10-04")
    # size per annotation popup
    driver.find_element_by_xpath("//a[@id='add_id_{}sizePerAnnotation']/img".format(id_infix)) \
      .click()  
    _fill_sizePerAnnotation_popup(driver, ss_path, current_id)
    driver.find_element_by_name("{}interannotatorAgreement".format(id_infix)).clear()
    driver.find_element_by_name("{}interannotatorAgreement".format(id_infix)).send_keys("Metric")
    driver.find_element_by_name("{}intraannotatorAgreement".format(id_infix)).clear()
    driver.find_element_by_name("{}intraannotatorAgreement".format(id_infix)).send_keys("Metric")
    # annotator popup
    Select(driver.find_element_by_xpath("//div[@class='form-row annotator']/div/select")) \
      .select_by_visible_text("personInfoType")
    _fill_annotator_popup(test, driver, ss_path, current_id)


def _fill_domains_form(driver, ss_path, id_infix):
    """
    fills the domains form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("{}domain".format(id_infix)).clear()
    driver.find_element_by_name("{}domain".format(id_infix)).send_keys("Domain")
    # size per domains popup
    driver.find_element_by_xpath("//a[@id='add_id_{}sizePerDomain']/img".format(id_infix)).click()  
    _fill_sizePerDomains_popup(driver, ss_path, current_id)
    Select(driver.find_element_by_name(
      "{}conformanceToClassificationScheme".format(id_infix))).select_by_visible_text(
      "UDC_classification")


def _fill_textClassifications_form(driver, ss_path, id_infix):
    """
    fills the annotations form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("{}textGenre".format(id_infix)).clear()
    driver.find_element_by_name("{}textGenre".format(id_infix)).send_keys("Genre")
    driver.find_element_by_name("{}textType".format(id_infix)).clear()
    driver.find_element_by_name("{}textType".format(id_infix)).send_keys("Type")
    driver.find_element_by_name("{}register".format(id_infix)).clear()
    driver.find_element_by_name("{}register".format(id_infix)).send_keys("Register")
    driver.find_element_by_name("{}subject_topic".format(id_infix)).clear()
    driver.find_element_by_name("{}subject_topic".format(id_infix)).send_keys("Topic")
    Select(driver.find_element_by_name(
      "{}conformanceToClassificationScheme".format(id_infix))).select_by_visible_text(
      "UDC_classification")
    # size per text classification popup
    driver.find_element_by_xpath("//a[@id='add_id_{}sizePerTextClassification']/img".format(id_infix)) \
      .click()  
    _fill_sizePerTextClassification_popup(driver, ss_path, current_id)


def _fill_timeCoverage_form(driver, ss_path, id_infix):
    """
    fills the time coverage form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("{}timeCoverage".format(id_infix)).clear()
    driver.find_element_by_name("{}timeCoverage".format(id_infix)).send_keys("coverage")
    # size per time coverage popup
    driver.find_element_by_xpath("//a[@id='add_id_{}sizePerTimeCoverage']/img".format(id_infix)).click()  
    _fill_sizePerTimeCoverage_popup(driver, ss_path, current_id)


def _fill_geographicCoverage_form(driver, ss_path, id_infix):
    """
    fills the geographic coverage form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("{}geographicCoverage".format(id_infix)).clear()
    driver.find_element_by_name("{}geographicCoverage".format(id_infix)).send_keys("coverage")
    # size per time coverage popup
    driver.find_element_by_xpath("//a[@id='add_id_{}sizePerGeographicCoverage']/img".format(id_infix)) \
      .click()  
    _fill_sizePerGeographicCoverage_popup(driver, ss_path, current_id)


def _fill_creation_form(driver, ss_path, id_infix):
    """
    fills the creation form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    # annotation tool popup
    driver.find_element_by_xpath("//a[@id='add_id_form-2-0-originalSource']/img".format(id_infix)) \
      .click()  
    _fill_originalSource_popup(driver, ss_path, current_id)
    Select(driver.find_element_by_name(
      "form-2-0-creationMode".format(id_infix))).select_by_visible_text("Automatic")
    driver.find_element_by_name("form-2-0-creationModeDetails".format(id_infix)).clear()
    driver.find_element_by_name("form-2-0-creationModeDetails".format(id_infix)).send_keys("Details")
    # creation tool popup
    driver.find_element_by_xpath("//a[@id='add_id_form-2-0-creationTool']/img".format(id_infix)) \
      .click()  
    _fill_creationTool_popup(driver, ss_path, current_id)


def _fill_linkToOtherMedias_form(driver, ss_path, id_infix):
    """
    fills the link to other medias form with required, recommended and optional information
    """
    driver.find_element_by_id("fieldsetcollapser2").click()
    Select(driver.find_element_by_name(
      "{}otherMedia".format(id_infix))).select_by_visible_text("Audio")
    driver.find_element_by_name("{}mediaTypeDetails".format(id_infix)).clear()
    driver.find_element_by_name("{}mediaTypeDetails".format(id_infix)).send_keys("Details")
    Select(driver.find_element_by_name(
      "{}synchronizedWithText".format(id_infix))).select_by_visible_text("No")
    Select(driver.find_element_by_name(
      "{}synchronizedWithAudio".format(id_infix))).select_by_visible_text("Yes")
    Select(driver.find_element_by_name(
      "{}synchronizedWithVideo".format(id_infix))).select_by_visible_text("No")
    Select(driver.find_element_by_name(
      "{}sycnhronizedWithImage".format(id_infix))).select_by_visible_text("No")
    Select(driver.find_element_by_name(
      "{}synchronizedWithTextNumerical".format(id_infix))).select_by_visible_text("No")


def _fill_resourceDocumentation_form(driver, ss_path, id_infix):
    """
    fills the resource documentation form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    # documentation popup
    Select(driver.find_element_by_xpath("//div[@class='form-row documentation']/div/select")) \
      .select_by_visible_text("documentInfoType")
    _fill_documentation_popup(driver, ss_path, current_id)
    driver.find_element_by_name("{}samplesLocation".format(id_infix)).clear()
    driver.find_element_by_name("{}samplesLocation".format(id_infix)).send_keys(
      "http://rn.samples.org")
    Select(driver.find_element_by_name(
      "{}toolDocumentationType_old".format(id_infix))).select_by_visible_text("Manual")
    driver.find_element_by_xpath("//div[@class='form-row toolDocumentationType']/div/div/div/a") \
      .click()


def _fill_resourceCreation_form(test, driver, ss_path, id_infix):
    """
    fills the resource creation form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    # resource creator popup
    Select(driver.find_element_by_xpath("//div[@class='form-row resourceCreator']/div/select")) \
      .select_by_visible_text("personInfoType")
    _fill_resourceCreator_popup(test, driver, ss_path, current_id)
    # funding project popup
    driver.find_element_by_xpath("//a[@id='add_id_{}fundingProject']/img".format(id_infix)).click()  
    _fill_fundingProject_popup(driver, ss_path, current_id)
    driver.find_element_by_name("{}creationStartDate".format(id_infix)).clear()
    driver.find_element_by_name("{}creationStartDate".format(id_infix)).send_keys("2012-09-28")
    driver.find_element_by_name("{}creationEndDate".format(id_infix)).clear()
    driver.find_element_by_name("{}creationEndDate".format(id_infix)).send_keys("2012-09-28")


def _fill_relations_form(driver, ss_path, id_infix):
    """
    fills the relations form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_name("{}relationType".format(id_infix)).clear()
    driver.find_element_by_name("{}relationType".format(id_infix)) \
      .send_keys("new type")
    # related resource popup
    driver.find_element_by_xpath("//a[@id='add_id_{}relatedResource']/img" \
      .format(id_infix)).click()  
    _fill_relatedResource_popup(driver, ss_path, current_id)


def _fill_validations_form(test, driver, ss_path, id_infix):
    """
    fills the validations form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    # documentation popup
    Select(driver.find_element_by_xpath("//div[@class='form-row validated']/div/select")) \
      .select_by_visible_text("Yes")
    Select(driver.find_element_by_xpath("//div[@class='form-row validationType']/div/select")) \
      .select_by_visible_text("Content")
    Select(driver.find_element_by_xpath("//div[@class='form-row validationMode']/div/select")) \
      .select_by_visible_text("Automatic")
    driver.find_element_by_name("{}validationModeDetails".format(id_infix)) \
      .clear()
    driver.find_element_by_name("{}validationModeDetails".format(id_infix)) \
      .send_keys("Additional information")
    Select(driver.find_element_by_xpath("//div[@class='form-row validationExtent']/div/select")) \
      .select_by_visible_text("Full")
    driver.find_element_by_name("{}validationExtentDetails".format(id_infix)) \
      .send_keys("Details")
    # size per validation popup
    driver.find_element_by_xpath("//a[@id='add_id_{}sizePerValidation']/img".format(id_infix)) \
      .click()  
    _fill_sizePerValidation_popup(driver, ss_path, current_id)
    # validation report popup
    Select(driver.find_element_by_xpath("//div[@class='form-row validationReport']/div/select")) \
      .select_by_visible_text("documentInfoType")
    _fill_validationReport_popup(driver, ss_path, current_id)
    # validation tool popup
    driver.find_element_by_xpath("//a[@id='add_id_{}validationTool']/img".format(id_infix)) \
      .click()  
    _fill_validationTool_popup(driver, ss_path, current_id)
    # validator popup
    Select(driver.find_element_by_xpath("//div[@class='form-row validator']/div/select")) \
      .select_by_visible_text("personInfoType")
    _fill_validator_popup(test, driver, ss_path, current_id)


def _fill_distribution_popup(test, driver, ss_path, parent_id):
    """
    fills the distribution popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_distributionInfo")
    test.spin_assert(lambda: test.assertEqual("Add Distribution",
        driver.find_element_by_css_selector("#content > h1").text))
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
    driver.find_element_by_name("licenceinfotype_model_set-0-downloadLocation") \
      .send_keys("http://mylicence.org")
    driver.find_element_by_name("licenceinfotype_model_set-0-executionLocation").clear()
    driver.find_element_by_name("licenceinfotype_model_set-0-executionLocation") \
      .send_keys("http://myexecution.org")
    driver.find_element_by_name("licenceinfotype_model_set-0-fee").clear()
    driver.find_element_by_name("licenceinfotype_model_set-0-fee").send_keys("1.10")
    driver.find_element_by_xpath("//div[@class='form-row attributionText']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_licenceinfotype_model_set-0-attributionText_0").clear()
    driver.find_element_by_name("key_licenceinfotype_model_set-0-attributionText_0").send_keys("en")
    driver.find_element_by_name("val_licenceinfotype_model_set-0-attributionText_0").clear()
    driver.find_element_by_name("val_licenceinfotype_model_set-0-attributionText_0") \
      .send_keys("The attribution text.")
    # licensor popup
    Select(driver.find_element_by_xpath("//div[@class='form-row licensor']/div/select")) \
      .select_by_visible_text("personInfoType")
    _fill_licensor_popup(test, driver, ss_path, current_id)
    test.spin_assert(lambda: test.assertEqual("Add Distribution",
        driver.find_element_by_css_selector("#content > h1").text))
    # distribution rights holder popup
    Select(driver.find_element_by_xpath("//div[@class='form-row distributionRightsHolder']/div/select")) \
      .select_by_visible_text("personInfoType")
    _fill_distributionRightsHolder_popup(test, driver, ss_path, current_id)
    test.spin_assert(lambda: test.assertEqual("Add Distribution",
        driver.find_element_by_css_selector("#content > h1").text))
    Select(driver.find_element_by_name(
      "licenceinfotype_model_set-0-userNature_old")).select_by_visible_text("Academic")
    driver.find_element_by_xpath(
      "//div[@class='form-row userNature']/div/div/ul/li/a") \
      .click()
    # membership popup
    driver.find_element_by_xpath("//a[@id='add_id_licenceinfotype_model_set-0-membershipInfo']/img") \
      .click()  
    _fill_membership_popup(driver, ss_path, current_id)
    # ipr holder popup
    Select(driver.find_element_by_xpath("//div[@class='form-row iprHolder']/div/select")) \
      .select_by_visible_text("personInfoType")
    _fill_iprHolder_popup(test, driver, ss_path, current_id)
    driver.find_element_by_name("availabilityStartDate").clear()
    driver.find_element_by_name("availabilityStartDate").send_keys("2012-10-02")
    driver.find_element_by_name("availabilityEndDate").clear()
    driver.find_element_by_name("availabilityEndDate").send_keys("2012-10-02")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_contactPerson_popup(test, driver, ss_path, parent_id):
    """
    fills the contact person popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_contactPerson")
    _fill_personInfo_form(test, driver, ss_path, "form-0-")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_personInfo_form(test, driver, ss_path, id_infix):
    """
    fills the person info form with required, recommended and optional information
    """
    test.spin_assert(lambda: test.assertEqual("Add Person",
        driver.find_element_by_css_selector("#content > h1").text))
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
    driver.find_element_by_name("{}email".format(id_infix)).clear()
    driver.find_element_by_name("{}email".format(id_infix)).send_keys("john.smith@institution.org")
    driver.find_element_by_name("{}url".format(id_infix)).clear()
    driver.find_element_by_name("{}url".format(id_infix)).send_keys("http://www.institution.org")
    driver.find_element_by_name("{}address".format(id_infix)).clear()
    driver.find_element_by_name("{}address".format(id_infix)).send_keys("1st main street")
    driver.find_element_by_name("{}zipCode".format(id_infix)).clear()
    driver.find_element_by_name("{}zipCode".format(id_infix)).send_keys("95000")
    driver.find_element_by_name("{}city".format(id_infix)).clear()
    driver.find_element_by_name("{}city".format(id_infix)).send_keys("somewhere")
    driver.find_element_by_name("{}region".format(id_infix)).clear()
    driver.find_element_by_name("{}region".format(id_infix)).send_keys("far away")
    driver.find_element_by_name("{}country".format(id_infix)).clear()
    driver.find_element_by_name("{}country".format(id_infix)).send_keys("world")
    driver.find_element_by_name("{}telephoneNumber".format(id_infix)).clear()
    driver.find_element_by_name("{}telephoneNumber".format(id_infix)).send_keys("1234567890")
    driver.find_element_by_name("{}faxNumber".format(id_infix)).clear()
    driver.find_element_by_name("{}faxNumber".format(id_infix)).send_keys("1234567890")
    driver.find_element_by_name("position").clear()
    driver.find_element_by_name("position").send_keys("Professor")
    # affiliation popup
    driver.find_element_by_css_selector("img[alt=\"Add Another\"]").click()
    _fill_affiliation_popup(test, driver, ss_path, current_id)


def _fill_affiliation_popup(test, driver, ss_path, parent_id):
    """
    fills the affiliation popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_affiliation")
    test.spin_assert(lambda: test.assertEqual("Add Organization",
        driver.find_element_by_css_selector("#content > h1").text))
    driver.find_element_by_name("key_organizationName_0").clear()
    driver.find_element_by_name("key_organizationName_0").send_keys("en")
    time.sleep(10)
    #test.spin_assert(lambda: test.assertEqual("en",
    #    driver.find_element_by_name("key_organizationName_0").text))
    driver.find_element_by_name("val_organizationName_0").clear()
    driver.find_element_by_name("val_organizationName_0").send_keys("Organization")
    driver.find_element_by_xpath("//div[@class='form-row organizationShortName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_organizationShortName_0").clear()
    driver.find_element_by_name("key_organizationShortName_0").send_keys("en")
    time.sleep(10)
    driver.find_element_by_name("val_organizationShortName_0").clear()
    driver.find_element_by_name("val_organizationShortName_0").send_keys("Short name")
    time.sleep(10)
    driver.find_element_by_xpath("//div[@class='form-row departmentName']/div/ul/li/a").click()
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    driver.find_element_by_name("key_departmentName_0").clear()
    driver.find_element_by_name("key_departmentName_0").send_keys("en")
    time.sleep(10)
    driver.find_element_by_name("val_departmentName_0").clear()
    driver.find_element_by_name("val_departmentName_0").send_keys("Department")
    time.sleep(10)
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


def _fill_usage_popup(driver, ss_path, parent_id):
    """
    fills the usage popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_usageInfo")
    current_id = driver.current_window_handle
    # access tool popup
    driver.find_element_by_xpath("//a[@id='add_id_accessTool']/img").click()  
    _fill_accessTool_popup(driver, ss_path, current_id)
    # resource associated with popup
    driver.find_element_by_xpath("//a[@id='add_id_resourceAssociatedWith']/img").click()  
    _fill_resourceAssociatedWith_popup(driver, ss_path, current_id)
    # foreseen use
    driver.find_element_by_id("fieldsetcollapser0").click()
    Select(driver.find_element_by_name("foreseenuseinfotype_model_set-0-foreseenUse")) \
      .select_by_visible_text("Human Use")
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
    # usage report popup
    Select(driver.find_element_by_name("subclass_select")).select_by_visible_text("documentInfoType")
    _fill_usageReport_popup(driver, ss_path, current_id)
    # derived resource popup
    driver.find_element_by_xpath("//a[@id='add_id_actualuseinfotype_model_set-0-derivedResource']/img").click()  
    _fill_derivedResource_popup(driver, ss_path, current_id)
    # project popup
    driver.find_element_by_xpath("//a[@id='add_id_actualuseinfotype_model_set-0-usageProject']/img").click()  
    _fill_project_popup(driver, ss_path, current_id)
    driver.find_element_by_name("actualuseinfotype_model_set-0-actualUseDetails").clear()
    driver.find_element_by_name("actualuseinfotype_model_set-0-actualUseDetails").send_keys("details")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_accessTool_popup(driver, ss_path, parent_id):
    """
    fills the access tool popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_accessTool")
    _fill_targetResource_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_targetResource_form(driver, ss_path):
    """
    fills the target resource form with required, recommended and optional information
    """
    driver.find_element_by_name("targetResourceNameURI").clear()
    driver.find_element_by_name("targetResourceNameURI").send_keys("578DFDG8DF")


def _fill_validationTool_popup(driver, ss_path, parent_id):
    """
    fills the validation tool popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_validationinfotype_model_set__dash__0__dash__validationTool")
    _fill_targetResource_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_annotationTool_popup(driver, ss_path, parent_id):
    """
    fills the annotation tool popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_annotationinfotype_model_set__dash__0__dash__annotationTool")
    _fill_targetResource_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_originalSource_popup(driver, ss_path, parent_id):
    """
    fills the original source popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_form__dash__2__dash__0__dash__originalSource")
    _fill_targetResource_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_creationTool_popup(driver, ss_path, parent_id):
    """
    fills the creation tool popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_form__dash__2__dash__0__dash__creationTool")
    _fill_targetResource_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_resourceAssociatedWith_popup(driver, ss_path, parent_id):
    """
    fills the resource associated with popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_resourceAssociatedWith")
    _fill_targetResource_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_usageReport_popup(driver, ss_path, parent_id):
    """
    fills the usage report popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_actualuseinfotype_model_set__dash__0__dash__usageReport")
    _fill_documentInfo_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_validationReport_popup(driver, ss_path, parent_id):
    """
    fills the validation report popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_validationinfotype_model_set__dash__0__dash__validationReport")
    _fill_documentInfo_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_documentation_popup(driver, ss_path, parent_id):
    """
    fills the documentation popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_form__dash__4__dash__0__dash__documentation")
    _fill_documentInfo_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_annotationManual_popup(driver, ss_path, parent_id):
    """
    fills the annotation manual popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_annotationinfotype_model_set__dash__0__dash__annotationManual")
    _fill_documentInfo_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_documentInfo_form(driver, ss_path):
    """
    fills the document info form with required, recommended and optional information
    """
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


def _fill_derivedResource_popup(driver, ss_path, parent_id):
    """
    fills the derived resource popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_actualuseinfotype_model_set__dash__0__dash__derivedResource")
    _fill_targetResource_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_relatedResource_popup(driver, ss_path, parent_id):
    """
    fills the related resource popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_relationinfotype_model_set__dash__0__dash__relatedResource")
    _fill_targetResource_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_project_popup(driver, ss_path, parent_id):
    """
    fills the project popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_actualuseinfotype_model_set__dash__0__dash__usageProject")
    _fill_projectInfo_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_fundingProject_popup(driver, ss_path, parent_id):
    """
    fills the funding project popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_form__dash__5__dash__0__dash__fundingProject")
    _fill_projectInfo_form(driver, ss_path)

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_projectInfo_form(driver, ss_path):
    """
    fills the project info form with required, recommended and optional information
    """
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


def _fill_metadataCreator_popup(test, driver, ss_path, parent_id):
    """
    fills the metadata creator popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_form__dash__2__dash__0__dash__metadataCreator")
    _fill_personInfo_form(test, driver, ss_path, "form-0-")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_resourceCreator_popup(test, driver, ss_path, parent_id):
    """
    fills the resource creator popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_form__dash__5__dash__0__dash__resourceCreator")
    _fill_personInfo_form(test, driver, ss_path, "form-0-")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_annotator_popup(test, driver, ss_path, parent_id):
    """
    fills the annotator popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_annotationinfotype_model_set__dash__0__dash__annotator")
    _fill_personInfo_form(test, driver, ss_path, "form-0-")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_iprHolder_popup(test, driver, ss_path, parent_id):
    """
    fills the ipr holder popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_iprHolder")
    _fill_personInfo_form(test, driver, ss_path, "form-0-")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_licensor_popup(test, driver, ss_path, parent_id):
    """
    fills the licensor popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_licenceinfotype_model_set__dash__0__dash__licensor")
    test.spin_assert(lambda: test.assertEqual("Add Person",
        driver.find_element_by_css_selector("#content > h1").text))
    _fill_personInfo_form(test, driver, ss_path, "form-0-")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_validator_popup(test, driver, ss_path, parent_id):
    """
    fills the validator popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_validationinfotype_model_set__dash__0__dash__validator")
    time.sleep(20)
    _fill_personInfo_form(test, driver, ss_path, "form-0-")
    time.sleep(20)
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_distributionRightsHolder_popup(test, driver, ss_path, parent_id):
    """
    fills the distributino rights holder popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_licenceinfotype_model_set__dash__0__dash__distributionRightsHolder")
    test.spin_assert(lambda: test.assertEqual("Add Person | META-SHARE backend",
        driver.get_title()))
    _fill_personInfo_form(test, driver, ss_path, "form-0-")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_membership_popup(driver, ss_path, parent_id):
    """
    fills the membership popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_licenceinfotype_model_set__dash__0__dash__membershipInfo")
    Select(driver.find_element_by_xpath("//div[@class='form-row member']/div/select")) \
      .select_by_visible_text("Yes")
    Select(driver.find_element_by_name(
      "membershipInstitution_old")).select_by_visible_text("LDC")
    driver.find_element_by_xpath("//div[@class='form-row membershipInstitution']/div/div/ul/li/a") \
      .click()

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_corpusTextInfo_popup(test, driver, ss_path, parent_id):
    """
    fills the corpus text info popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_corpusTextInfo__dash__0")
    # required fields
    # corpus text info / linguality
    _fill_linguality_form(driver, ss_path, "form-0-")
    # corpus text info / language
    _fill_language_form(driver, ss_path, "languageinfotype_model_set-0-")
    # corpus text info / size
    _fill_textSize_form(driver, ss_path, "sizeinfotype_model_set-0-")
    # recommended fields
    driver.find_element_by_css_selector("a[href=\"#field-2\"]").click()
    # corpus text info / modalities
    _fill_modalities_form(driver, ss_path, "modalityinfotype_model_set-0-")
    # corpus text info / text formats
    _fill_textFormats_form(driver, ss_path, "textformatinfotype_model_set-0-")
    # corpus text info / character encodings
    _fill_characterEncodings_form(driver, ss_path, "characterencodinginfotype_model_set-0-")
    # show annotations
    driver.find_element_by_id("fieldsetcollapser0").click()
    # corpus text info / annotations
    _fill_annotations_form(test, driver, ss_path, "annotationinfotype_model_set-0-")
    # corpus text info / domains
    _fill_domains_form(driver, ss_path, "domaininfotype_model_set-0-")
    # show text classifications
    driver.find_element_by_id("fieldsetcollapser1").click()
    # corpus text info / text classifications
    _fill_textClassifications_form(driver, ss_path, "textclassificationinfotype_model_set-0-")
    # corpus text info / time coverage
    _fill_timeCoverage_form(driver, ss_path, "timecoverageinfotype_model_set-0-")
    # corpus text info / geographic coverage
    _fill_geographicCoverage_form(driver, ss_path, "geographiccoverageinfotype_model_set-0-")
    # corpus text info / creation
    _fill_creation_form(driver, ss_path, "creationinfotype_model_set-0-")
    # optional fields
    driver.find_element_by_css_selector("a[href=\"#field-3\"]").click()
    # corpus text info / link to other media
    _fill_linkToOtherMedias_form(driver, ss_path, "linktoothermediainfotype_model_set-0-")

    # save and close corpus text info popup
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_corpusAudioInfo_popup(driver, ss_path, parent_id):
    """
    fills the corpus audio info popup with all required
    information and returns to the parent window
    """
    driver.switch_to.window("id_corpusAudioInfo")
    Select(driver.find_element_by_id("id_form-0-lingualityType")).select_by_visible_text(
      "Monolingual")
    # corpus audio info / language
    _fill_language_form(driver, ss_path, "languageinfotype_model_set-0-")
    # corpus audio info / size popup
    driver.find_element_by_css_selector("#add_id_audioSizeInfo > img[alt=\"Add Another\"]").click()
    _fill_audioSize_form(driver, ss_path, "id_corpusAudioInfo")

    # save and close corpus audio info popup
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_corpusVideoInfo_popup(driver, ss_path, parent_id):
    """
    fills the corpus video info popup with all required
    information and returns to the parent window
    """
    driver.find_element_by_id("add_id_corpusVideoInfo-0").click()
    driver.switch_to.window("id_corpusVideoInfo__dash__0")
    # corpus video info / size popup
    driver.find_element_by_name("sizeinfotype_model_set-0-size").clear()
    driver.find_element_by_name("sizeinfotype_model_set-0-size").send_keys("100")
    driver.find_element_by_name("sizeinfotype_model_set-0-sizeUnit").send_keys("Gb")

    # save and close corpus video info popup
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)
        

def _fill_corpusImageInfo_popup(driver, ss_path, parent_id):
    """
    fills the corpus image info popup with all required
    information and returns to the parent window
    """
    driver.switch_to.window("id_corpusImageInfo")
    # corpus image info / size popup
    driver.find_element_by_name("sizeinfotype_model_set-0-size").clear()
    driver.find_element_by_name("sizeinfotype_model_set-0-size").send_keys("100")
    driver.find_element_by_name("sizeinfotype_model_set-0-sizeUnit").send_keys("Gb")

    # save and close corpus image info popup
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_corpusTextNumericalInfo_popup(driver, ss_path, parent_id):
    """
    fills the corpus text numerical info popup with all required
    information and returns to the parent window
    """
    driver.switch_to.window("id_corpusTextNumericalInfo")

    # save and close corpus text numerical info popup
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_corpusTextNgramInfo_popup(driver, ss_path, parent_id):
    """
    fills the corpus text ngram info popup with all required
    information and returns to the parent window
    """
    driver.switch_to.window("id_corpusTextNgramInfo")
    # corpus ngram info / base item
    Select(driver.find_element_by_name("form-0-baseItem_old")).select_by_visible_text("Other")
    driver.find_element_by_xpath("//a[@class='selector-add']").click()
    # corpus ngram info / order
    driver.find_element_by_name("form-0-order").clear()
    driver.find_element_by_name("form-0-order").send_keys("5")
    # corpus ngram info / linguality type
    Select(driver.find_element_by_id("id_form-2-0-lingualityType")).select_by_visible_text(
      "Monolingual")
    # corpus ngram info / language
    _fill_language_form(driver, ss_path, "languageinfotype_model_set-0-")
    # corpus ngram info / size popup
    driver.find_element_by_name("sizeinfotype_model_set-0-size").clear()
    driver.find_element_by_name("sizeinfotype_model_set-0-size").send_keys("100")
    driver.find_element_by_name("sizeinfotype_model_set-0-sizeUnit").send_keys("Gb")
    # save and close corpus ngram info popup
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_corpusLanguageDescriptionGeneralInfo_popup(driver, ss_path, parent_id):
    """
    fills the language description general info popup with all required
    information and returns to the parent window
    """
    driver.switch_to.window("edit_id_langdescInfo")
    Select(driver.find_element_by_id("id_languageDescriptionType")).select_by_visible_text(
      "Grammar")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time())) 
    save_and_close(driver, parent_id)


def _fill_corpusLanguageDescriptionTextInfo_popup(driver, ss_path, parent_id):
    """
    fills the language description info text popup with all required
    information and returns to the parent window
    """
    driver.switch_to.window("id_languageDescriptionTextInfo")
    Select(driver.find_element_by_id("id_form-2-0-lingualityType")).select_by_visible_text(
      "Monolingual")
    # language description info text / language
    _fill_language_form(driver, ss_path, "languageinfotype_model_set-0-")

    # save and close language description info text popup
    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_linguality_form(driver, ss_path, id_infix):
    """
    fills the linguality with required, recommended and optional information
    """
    Select(driver.find_element_by_id("id_{}lingualityType".format(id_infix))).select_by_visible_text(
      "Monolingual")
    Select(driver.find_element_by_id("id_{}multilingualityType".format(id_infix))).select_by_visible_text(
      "Other")
    driver.find_element_by_id("id_{}multilingualityTypeDetails".format(id_infix)).clear()
    driver.find_element_by_id("id_{}multilingualityTypeDetails".format(id_infix)).send_keys("Information")


def _fill_language_form(driver, ss_path, id_infix):
    """
    fills the language form with required, recommended and optional information
    """
    # remember current window id
    current_id = driver.current_window_handle
    driver.find_element_by_id("id_{}languageId".format(id_infix)).clear()
    driver.find_element_by_id("id_{}languageId".format(id_infix)).send_keys("De")
    driver.find_element_by_id("id_{}languageName".format(id_infix)).clear()
    driver.find_element_by_id("id_{}languageName".format(id_infix)).send_keys("German")
    driver.find_element_by_id("id_{}languageScript".format(id_infix)).clear()
    driver.find_element_by_id("id_{}languageScript".format(id_infix)).send_keys("Script")
    # size per language popup
    driver.find_element_by_xpath("//a[@id='add_id_languageinfotype_model_set-0-sizePerLanguage']/img").click()
    _fill_sizePerLanguage_popup(driver, ss_path, current_id)
    # language variety popup
    driver.find_element_by_xpath("//a[@id='add_id_languageinfotype_model_set-0-languageVarietyInfo']/img").click()
    _fill_languageVariety_popup(driver, ss_path, current_id)


def _fill_sizePerLanguage_popup(driver, ss_path, parent_id):
    """
    fills the size per language popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_languageinfotype_model_set__dash__0__dash__sizePerLanguage")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_sizePerModalities_popup(driver, ss_path, parent_id):
    """
    fills the size per modalities popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_modalityinfotype_model_set__dash__0__dash__sizePerModality")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_sizePerTextFormats_popup(driver, ss_path, parent_id):
    """
    fills the size per text formats popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_textformatinfotype_model_set__dash__0__dash__sizePerTextFormat")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_sizePerCharacterEncodings_popup(driver, ss_path, parent_id):
    """
    fills the size per character encodings popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_characterencodinginfotype_model_set__dash__0__dash__sizePerCharacterEncoding")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_sizePerDomains_popup(driver, ss_path, parent_id):
    """
    fills the size per domains popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_domaininfotype_model_set__dash__0__dash__sizePerDomain")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_size_form(driver, ss_path, id_infix):
    """
    fills the size form with required, recommended and optional information
    """
    driver.find_element_by_id("id_{}size".format(id_infix)).clear()
    driver.find_element_by_id("id_{}size".format(id_infix)).send_keys("12")
    Select(driver.find_element_by_xpath("//div[@class='form-row sizeUnit']/div/select")) \
      .select_by_visible_text("Gb")


def _fill_languageVariety_popup(driver, ss_path, parent_id):
    """
    fills the language variety popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_languageinfotype_model_set__dash__0__dash__languageVarietyInfo")
    Select(driver.find_element_by_id("id_languageVarietyType")).select_by_visible_text("Jargon")
    driver.find_element_by_id("id_languageVarietyName").clear()
    driver.find_element_by_id("id_languageVarietyName").send_keys("Jargon name")
    _fill_size_form(driver, ss_path, "form-0-")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_textSize_form(driver, ss_path, id_infix):
    """
    fills the text size with required information
    """
    driver.find_element_by_id("id_{}size".format(id_infix)).clear()
    driver.find_element_by_id("id_{}size".format(id_infix)).send_keys("10000")
    Select(driver.find_element_by_id("id_{}sizeUnit".format(id_infix))).select_by_visible_text("Tokens")


def _fill_audioSize_form(driver, ss_path, parent_id):
    """
    fills the text size with required information
    """
    driver.switch_to.window("id_audioSizeInfo")
    driver.find_element_by_id("id_sizeinfotype_model_set-0-size").send_keys("100")
    Select(driver.find_element_by_id("id_sizeinfotype_model_set-0-sizeUnit")).select_by_visible_text("Gb")
    save_and_close(driver, parent_id) 


def _fill_sizePerValidation_popup(driver, ss_path, parent_id):
    """
    fills the size per validation popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_validationinfotype_model_set__dash__0__dash__sizePerValidation")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_sizePerAnnotation_popup(driver, ss_path, parent_id):
    """
    fills the size per annotation popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_annotationinfotype_model_set__dash__0__dash__sizePerAnnotation")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_sizePerTextClassification_popup(driver, ss_path, parent_id):
    """
    fills the size per text classification popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_textclassificationinfotype_model_set__dash__0__dash__sizePerTextClassification")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_sizePerTimeCoverage_popup(driver, ss_path, parent_id):
    """
    fills the size per time coverage popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_timecoverageinfotype_model_set__dash__0__dash__sizePerTimeCoverage")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _fill_sizePerGeographicCoverage_popup(driver, ss_path, parent_id):
    """
    fills the size per geographic coverage popup with all required, recommended and optional
    information and returns to the parent window
    """
    driver.switch_to.window("id_geographiccoverageinfotype_model_set__dash__0__dash__sizePerGeographicCoverage")
    _fill_size_form(driver, ss_path, "")

    driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
    save_and_close(driver, parent_id)


def _ingest(driver):
    """
    selects all resources and ingests them
    """
    driver.find_element_by_id("action-toggle").click()
    Select(driver.find_element_by_name("action")) \
        .select_by_visible_text("Ingest selected internal resources")
    driver.find_element_by_name("index").click()


def _publish(driver):
    """
    selects all resources and publishes them
    """
    driver.find_element_by_id("action-toggle").click()
    Select(driver.find_element_by_name("action")) \
        .select_by_visible_text("Publish selected ingested resources")
    driver.find_element_by_name("index").click()


def _delete(driver):
    """
    selects all resources and deletes them
    """
    driver.find_element_by_id("action-toggle").click()
    Select(driver.find_element_by_name("action")) \
        .select_by_visible_text("Mark selected resources as deleted")
    driver.find_element_by_name("index").click()
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
