from django_selenium.testcases import SeleniumTestCase
from metashare import settings, test_utils
from metashare.repository.seltests.test_utils import setup_screenshots_folder, \
    import_dir, click_and_wait
from metashare.settings import DJANGO_BASE, ROOT_PATH
import time
from django.core.management import call_command
from selenium.webdriver.support.select import Select


TESTFIXTURE_XML = '{}/repository/test_fixtures/ELRA/'.format(ROOT_PATH)

class FilterTest(SeleniumTestCase):

    def setUp(self):
        # make sure the index does not contain any stale entries
        call_command('rebuild_index', interactive=False, using=settings.TEST_MODE_NAME)
        # load test fixture; status will be set 'published'
        test_utils.setup_test_storage()
        import_dir(TESTFIXTURE_XML)

        super(FilterTest, self).setUp()
        self.base_url = 'http://{}:{}/{}' \
            .format(self.testserver_host, self.testserver_port, DJANGO_BASE)


    def tearDown(self):
        test_utils.clean_resources_db()
        test_utils.clean_storage()

        super(FilterTest, self).tearDown()


    def test_filter(self):
        ss_path = setup_screenshots_folder(
          "PNG-metashare.repository.seltests.test_editor.FilterTest",
          "test_filter")

        driver = self.driver
        driver.get(self.base_url)
        # TODO remove this workaround when Selenium starts working again as intended
        driver.set_window_size(1280, 1024)
        # click 'browse'
        driver.find_element_by_xpath("//div[@id='header']/ul/li[1]/a").click()
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        self.assertEqual("19 Language Resources", driver.find_element_by_css_selector("h3").text)
        # make sure all filters are available
        self.assertEqual("Language", driver.find_element_by_link_text("Language").text)
        self.assertEqual("Resource Type", driver.find_element_by_link_text("Resource Type").text)
        self.assertEqual("Media Type", driver.find_element_by_link_text("Media Type").text)
        self.assertEqual("Availability", driver.find_element_by_link_text("Availability").text)
        self.assertEqual("Licence", driver.find_element_by_link_text("Licence").text)
        self.assertEqual("Restrictions of Use", driver.find_element_by_link_text("Restrictions of Use").text)
        self.assertEqual("Validated", driver.find_element_by_link_text("Validated").text)
        self.assertEqual("Foreseen Use", driver.find_element_by_link_text("Foreseen Use").text)
        self.assertEqual("Use Is NLP Specific", driver.find_element_by_link_text("Use Is NLP Specific").text)
        self.assertEqual("Linguality Type", driver.find_element_by_link_text("Linguality Type").text)
        self.assertEqual("Multilinguality Type", driver.find_element_by_link_text("Multilinguality Type").text)
        self.assertEqual("Modality Type", driver.find_element_by_link_text("Modality Type").text)
        self.assertEqual("MIME Type", driver.find_element_by_link_text("MIME Type").text)
        self.assertEqual("Conformance to Standards/Best Practices", driver \
          .find_element_by_link_text("Conformance to Standards/Best Practices").text)
        self.assertEqual("Domain", driver.find_element_by_link_text("Domain").text)
        self.assertEqual("Geographic Coverage", driver.find_element_by_link_text("Geographic Coverage").text)
        self.assertEqual("Time Coverage", driver.find_element_by_link_text("Time Coverage").text)
        self.assertEqual("Subject", driver.find_element_by_link_text("Subject").text)
        self.assertEqual("Language Variety", driver.find_element_by_link_text("Language Variety").text)
        
        # check Language filter
        click_and_wait(driver.find_element_by_link_text("Language"))
        self.assertEqual("English (9)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[1]").text)
        self.assertEqual("Spanish (6)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[2]").text)
        self.assertEqual("French (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[3]").text)
        self.assertEqual("Italian (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[4]").text)
        self.assertEqual("German (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[5]").text)
        self.assertEqual("more", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[14]").text)
        # check language filter more/less
        click_and_wait(driver.find_element_by_link_text("more"))
        self.assertEqual("Portuguese (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[6]").text)
        self.assertEqual("Arabic (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[7]").text)
        self.assertEqual("Bulgarian (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[8]").text)
        self.assertEqual("Chinese (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[9]").text)
        self.assertEqual("Estonian (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[10]").text)
        self.assertEqual("Polish (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[11]").text)
        self.assertEqual("Thai (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[12]").text)
        self.assertEqual("Turkish (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[13]").text)
        self.assertEqual("less", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[14]").text)
        click_and_wait(driver.find_element_by_link_text("less"))
        self.assertEqual("more", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[14]").text)
        click_and_wait(driver.find_element_by_link_text("Language"))
        
        # check Resource Type filter        
        click_and_wait(driver.find_element_by_link_text("Resource Type"))
        self.assertEqual("Corpus (10)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[4]/div[1]").text)
        self.assertEqual("Lexical Conceptual Resource (9)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[4]/div[2]").text)
        click_and_wait(driver.find_element_by_link_text("Resource Type"))
        
        # check Media Type filter        
        click_and_wait(driver.find_element_by_link_text("Media Type"))
        self.assertEqual("Text (13)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[6]/div[1]").text)
        self.assertEqual("Audio (6)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[6]/div[2]").text)
        click_and_wait(driver.find_element_by_link_text("Media Type"))
        
        # check Availability filter
        click_and_wait(driver.find_element_by_link_text("Availability"))
        self.assertEqual("Available - Restricted Use (19)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[8]/div").text)
        click_and_wait(driver.find_element_by_link_text("Availability"))
        
        # check Licence filter
        click_and_wait(driver.find_element_by_link_text("Licence"))
        self.assertEqual("ELRA_VAR (14)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[1]").text)
        self.assertEqual("ELRA_END_USER (13)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[2]").text)
        self.assertEqual("ELRA_EVALUATION (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[3]").text)
        self.assertEqual("CC_BY (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[4]").text)
        self.assertEqual("Proprietary (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[5]").text)
        click_and_wait(driver.find_element_by_link_text("Licence"))
       
        # check Restrictions of Use filter        
        click_and_wait(driver.find_element_by_link_text("Restrictions of Use"))
        self.assertEqual("Commercial Use (14)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[12]/div[1]").text)
        self.assertEqual("Academic - Non Commercial Use (13)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[12]/div[2]").text)
        self.assertEqual("Evaluation Use (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[12]/div[3]").text)
        self.assertEqual("Attribution (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[12]/div[4]").text)
        click_and_wait(driver.find_element_by_link_text("Restrictions of Use"))
       
        # check Validated filter        
        click_and_wait(driver.find_element_by_link_text("Validated"))
        self.assertEqual("True (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[14]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Validated"))
        
        # check Foreseen Use filter        
        click_and_wait(driver.find_element_by_link_text("Foreseen Use"))
        self.assertEqual("Nlp Applications (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[16]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Foreseen Use"))
        
        # check Use Is NLP Specific filter        
        click_and_wait(driver.find_element_by_link_text("Use Is NLP Specific"))
        self.assertEqual("Speech Synthesis (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[18]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Use Is NLP Specific"))
        
        # check Linguality Type filter        
        click_and_wait(driver.find_element_by_link_text("Linguality Type"))
        self.assertEqual("Monolingual (18)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[20]/div[1]").text)
        self.assertEqual("Bilingual (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[20]/div[2]").text)
        click_and_wait(driver.find_element_by_link_text("Linguality Type"))
        
        # check Multilinguality Type filter        
        click_and_wait(driver.find_element_by_link_text("Multilinguality Type"))
        self.assertEqual("Parallel (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[22]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Multilinguality Type"))
        
        # check Modality Type filter        
        click_and_wait(driver.find_element_by_link_text("Modality Type"))
        self.assertEqual("Other (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[24]/div[1]").text)
        self.assertEqual("Written Language (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[24]/div[2]").text)
        click_and_wait(driver.find_element_by_link_text("Modality Type"))
        
        # check MIME Type filter        
        click_and_wait(driver.find_element_by_link_text("MIME Type"))
        self.assertEqual("Plain text (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[26]/div[1]").text)
        self.assertEqual("Text/xml (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[26]/div[2]").text)
        self.assertEqual("Txt/plain (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[26]/div[3]").text)
        click_and_wait(driver.find_element_by_link_text("MIME Type"))
        
        # check Conformance to Standards/Best Practices filter        
        click_and_wait(driver.find_element_by_link_text("Conformance to Standards/Best Practices"))
        self.assertEqual("TEI (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[28]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Conformance to Standards/Best Practices"))
        
        # check Domain filter        
        click_and_wait(driver.find_element_by_link_text("Domain"))
        self.assertEqual("General (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[30]/div[1]").text)
        self.assertEqual("Law_politics (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[30]/div[2]").text)
        self.assertEqual("Science (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[30]/div[3]").text)
        click_and_wait(driver.find_element_by_link_text("Domain"))
        
        # check Geographic Coverage filter        
        click_and_wait(driver.find_element_by_link_text("Geographic Coverage"))
        self.assertEqual("European Union (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[32]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Geographic Coverage"))
        
        # check Time Coverage filter        
        click_and_wait(driver.find_element_by_link_text("Time Coverage"))
        self.assertEqual("1958-2006 (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[34]/div[1]").text)
        self.assertEqual("2003-2011 (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[34]/div[2]").text)
        self.assertEqual("2004-2011 (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[34]/div[3]").text)
        click_and_wait(driver.find_element_by_link_text("Time Coverage"))
        
        # check Subject filter        
        click_and_wait(driver.find_element_by_link_text("Subject"))
        self.assertEqual("News (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[36]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Subject"))
        
        # check Language Variety filter        
        click_and_wait(driver.find_element_by_link_text("Language Variety"))
        self.assertEqual("Castilian (6)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[38]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Language Variety"))
        
        # test sorting:
        # default sorting is by resource name, ascending
        self.assertEqual("Resource Name A-Z", driver.find_element_by_xpath(
          # first option is selected by default
          "//select[@name='ordering']/option[1]").text)
        self.assertEqual("AURORA-5", driver.find_element_by_xpath(
          "//div[@class='results']/div/a").text)
        # now sort by Resource name descending
        Select(driver.find_element_by_name("ordering")).select_by_visible_text("Resource Name Z-A")
        self.assertEqual("VERBA Polytechnic and Plurilingual Terminological Database - S-AA Anatomy", driver.find_element_by_xpath(
          "//div[@class='results']/div/a").text)
        # now sort by resource type ascending
        Select(driver.find_element_by_name("ordering")).select_by_visible_text("Resource Type A-Z")
        self.assertEqual("Corpus", driver.find_element_by_xpath(
          "//div[@class='results']/div/img").get_attribute("title"))
        # now sort by resource type descending
        Select(driver.find_element_by_name("ordering")).select_by_visible_text("Resource Type Z-A")
        self.assertEqual("Lexical Conceptual", driver.find_element_by_xpath(
          "//div[@class='results']/div/img").get_attribute("title"))
        # now sort by media type ascending
        Select(driver.find_element_by_name("ordering")).select_by_visible_text("Media Type A-Z")
        self.assertEqual("audio", driver.find_element_by_xpath(
          "//div[@class='results']/div/img[2]").get_attribute("title"))
        # now sort by media type descending
        Select(driver.find_element_by_name("ordering")).select_by_visible_text("Media Type Z-A")
        self.assertEqual("text", driver.find_element_by_xpath(
          "//div[@class='results']/div/img[2]").get_attribute("title"))
        # now sort by language ascending
        Select(driver.find_element_by_name("ordering")).select_by_visible_text("Language Name A-Z")
        self.assertEqual("Arabic\nEnglish\nFrench", driver.find_element_by_xpath(
          "//div[@class='results']/div/ul").text)
        # now sort by language descending
        Select(driver.find_element_by_name("ordering")).select_by_visible_text("Language Name Z-A")
        self.assertEqual("Turkish", driver.find_element_by_xpath(
          "//div[@class='results']/div/ul").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        
        # test filter application:
        # filter by language English
        driver.find_element_by_link_text("Language").click()
        driver.find_element_by_link_text("English").click()
        self.assertEqual("9 Language Resources", driver.find_element_by_css_selector("h3").text)
        # additionally filter by license
        driver.find_element_by_link_text("Licence").click()
        driver.find_element_by_link_text("ELRA_VAR").click()
        self.assertEqual("5 Language Resources", driver.find_element_by_css_selector("h3").text)
        # addtionally filter by media type
        driver.find_element_by_link_text("Media Type").click()
        driver.find_element_by_link_text("Text").click()
        self.assertEqual("4 Language Resources", driver.find_element_by_css_selector("h3").text)
        # additionally filter by restriction of use
        driver.find_element_by_link_text("Restrictions of Use").click()
        driver.find_element_by_link_text("Commercial Use").click()
        self.assertEqual("4 Language Resources", driver.find_element_by_css_selector("h3").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # remove language filter
        driver.find_element_by_link_text("English").click()
        self.assertEqual("9 Language Resources", driver.find_element_by_css_selector("h3").text)
        # remove license filter
        driver.find_element_by_link_text("ELRA_VAR").click()
        self.assertEqual("9 Language Resources", driver.find_element_by_css_selector("h3").text)
        # remove media type filter
        driver.find_element_by_link_text("Text").click()
        self.assertEqual("14 Language Resources", driver.find_element_by_css_selector("h3").text)
        # remove restiriction of use filter
        driver.find_element_by_link_text("Commercial Use").click()
        self.assertEqual("19 Language Resources", driver.find_element_by_css_selector("h3").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        
        
