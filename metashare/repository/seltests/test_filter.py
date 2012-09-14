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
        self.assertEqual("29 Language Resources (Page 1 of 2)", driver.find_element_by_css_selector("h3").text)

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
        self.assertEqual("English (10)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[1]").text)
        self.assertEqual("Spanish (7)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[2]").text)
        self.assertEqual("Modern Greek (1453-) (5)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[3]").text)
        self.assertEqual("Italian (4)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[4]").text)
        self.assertEqual("French (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[5]").text)
        self.assertEqual("more", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[15]").text)
        # check language filter more/less
        click_and_wait(driver.find_element_by_link_text("more"))
        self.assertEqual("Bulgarian (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[6]").text)
        self.assertEqual("German (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[7]").text)
        self.assertEqual("Polish (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[8]").text)
        self.assertEqual("Portuguese (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[9]").text)
        self.assertEqual("Arabic (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[10]").text)
        self.assertEqual("Chinese (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[11]").text)
        self.assertEqual("Estonian (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[12]").text)
        self.assertEqual("Thai (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[13]").text)
        self.assertEqual("Turkish (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[14]").text)
        self.assertEqual("less", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[15]").text)
        click_and_wait(driver.find_element_by_link_text("less"))
        self.assertEqual("more", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[2]/div[15]").text)
        click_and_wait(driver.find_element_by_link_text("Language"))
        
        # check Resource Type filter        
        click_and_wait(driver.find_element_by_link_text("Resource Type"))
        self.assertEqual("Corpus (15)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[4]/div[1]").text)
        self.assertEqual("Lexical Conceptual Resource (11)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[4]/div[2]").text)
        self.assertEqual("Tool Service (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[4]/div[3]").text)
        click_and_wait(driver.find_element_by_link_text("Resource Type"))
        
        # check Media Type filter        
        click_and_wait(driver.find_element_by_link_text("Media Type"))
        self.assertEqual("Text (23)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[6]/div[1]").text)
        self.assertEqual("Audio (8)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[6]/div[2]").text)
        self.assertEqual("Image (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[6]/div[3]").text)
        self.assertEqual("Video (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[6]/div[4]").text)
        click_and_wait(driver.find_element_by_link_text("Media Type"))
        
        # check Availability filter
        click_and_wait(driver.find_element_by_link_text("Availability"))
        self.assertEqual("Available - Restricted Use (25)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[8]/div[1]").text)
        self.assertEqual("Available - Unrestricted Use (4)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[8]/div[2]").text)
        click_and_wait(driver.find_element_by_link_text("Availability"))
        
        # check Licence filter
        click_and_wait(driver.find_element_by_link_text("Licence"))
        self.assertEqual("ELRA_VAR (15)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[1]").text)
        self.assertEqual("ELRA_END_USER (13)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[2]").text)
        self.assertEqual("Proprietary (6)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[3]").text)
        self.assertEqual("ELRA_EVALUATION (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[4]").text)
        self.assertEqual("BSD - Style (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[10]/div[5]").text)
        click_and_wait(driver.find_element_by_link_text("Licence"))
       
        # check Restrictions of Use filter        
        click_and_wait(driver.find_element_by_link_text("Restrictions of Use"))
        self.assertEqual("Academic - Non Commercial Use (17)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[12]/div[1]").text)
        self.assertEqual("Commercial Use (15)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[12]/div[2]").text)
        self.assertEqual("Evaluation Use (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[12]/div[3]").text)
        self.assertEqual("Attribution (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[12]/div[4]").text)
        self.assertEqual("Share Alike (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[12]/div[5]").text)
        click_and_wait(driver.find_element_by_link_text("Restrictions of Use"))
       
        # check Validated filter        
        click_and_wait(driver.find_element_by_link_text("Validated"))
        self.assertEqual("True (6)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[14]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Validated"))
        
        # check Foreseen Use filter        
        click_and_wait(driver.find_element_by_link_text("Foreseen Use"))
        self.assertEqual("Nlp Applications (8)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[16]/div[1]").text)
        self.assertEqual("Human Use (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[16]/div[2]").text)
        click_and_wait(driver.find_element_by_link_text("Foreseen Use"))
        
        # check Use Is NLP Specific filter        
        click_and_wait(driver.find_element_by_link_text("Use Is NLP Specific"))
        self.assertEqual("Other (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[18]/div[1]").text)
        self.assertEqual("Contradiction Detection (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[18]/div[2]").text)
        self.assertEqual("Emotion Recognition (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[18]/div[3]").text)
        self.assertEqual("Expression Recognition (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[18]/div[4]").text)
        self.assertEqual("Face Recognition (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[18]/div[5]").text)
        click_and_wait(driver.find_element_by_link_text("Use Is NLP Specific"))
        
        # check Linguality Type filter        
        click_and_wait(driver.find_element_by_link_text("Linguality Type"))
        self.assertEqual("Monolingual (24)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[20]/div[1]").text)
        self.assertEqual("Bilingual (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[20]/div[2]").text)
        click_and_wait(driver.find_element_by_link_text("Linguality Type"))
        
        # check Multilinguality Type filter        
        click_and_wait(driver.find_element_by_link_text("Multilinguality Type"))
        self.assertEqual("Comparable (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[22]/div[1]").text)
        self.assertEqual("Parallel (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[22]/div[2]").text)
        click_and_wait(driver.find_element_by_link_text("Multilinguality Type"))
        
        # check Modality Type filter        
        click_and_wait(driver.find_element_by_link_text("Modality Type"))
        self.assertEqual("Written Language (6)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[24]/div[1]").text)
        self.assertEqual("Spoken Language (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[24]/div[2]").text)
        self.assertEqual("Body Gesture (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[24]/div[3]").text)
        self.assertEqual("Combination Of Modalities (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[24]/div[4]").text)
        self.assertEqual("Facial Expression (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[24]/div[5]").text)
        click_and_wait(driver.find_element_by_link_text("Modality Type"))
        
        # check MIME Type filter        
        click_and_wait(driver.find_element_by_link_text("MIME Type"))
        self.assertEqual("Plain text (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[26]/div[1]").text)
        self.assertEqual("Audio/ PCMA (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[26]/div[2]").text)
        self.assertEqual("Text/plain (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[26]/div[3]").text)
        self.assertEqual("Text/txt (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[26]/div[4]").text)
        self.assertEqual("Text/xml (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[26]/div[5]").text)
        click_and_wait(driver.find_element_by_link_text("MIME Type"))
        
        # check Conformance to Standards/Best Practices filter        
        click_and_wait(driver.find_element_by_link_text("Conformance to Standards/Best Practices"))
        self.assertEqual("Other (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[28]/div[1]").text)
        self.assertEqual("TEI (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[28]/div[2]").text)
        self.assertEqual("XCES (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[28]/div[3]").text)
        self.assertEqual("EAGLES (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[28]/div[4]").text)
        self.assertEqual("EML (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[28]/div[5]").text)
        click_and_wait(driver.find_element_by_link_text("Conformance to Standards/Best Practices"))
        
        # check Domain filter        
        click_and_wait(driver.find_element_by_link_text("Domain"))
        self.assertEqual("General (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[30]/div[1]").text)
        self.assertEqual("Science (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[30]/div[2]").text)
        self.assertEqual("EU parliamentary sessions (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[30]/div[3]").text)
        self.assertEqual("Business (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[30]/div[4]").text)
        self.assertEqual("Fiction (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[30]/div[5]").text)
        click_and_wait(driver.find_element_by_link_text("Domain"))
        
        # check Geographic Coverage filter        
        click_and_wait(driver.find_element_by_link_text("Geographic Coverage"))
        self.assertEqual("European Union (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[32]/div[1]").text)
        self.assertEqual("Thrace (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[32]/div[2]").text)
        click_and_wait(driver.find_element_by_link_text("Geographic Coverage"))
        
        # check Time Coverage filter        
        click_and_wait(driver.find_element_by_link_text("Time Coverage"))
        self.assertEqual("1958-2006 (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[34]/div[1]").text)
        self.assertEqual("2003-2011 (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[34]/div[2]").text)
        self.assertEqual("2004-2011 (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[34]/div[3]").text)
        self.assertEqual("After 1990 (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[34]/div[4]").text)
        click_and_wait(driver.find_element_by_link_text("Time Coverage"))
        
        # check Subject filter        
        click_and_wait(driver.find_element_by_link_text("Subject"))
        self.assertEqual("News (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[36]/div[1]").text)
        click_and_wait(driver.find_element_by_link_text("Subject"))
        
        # check Language Variety filter        
        click_and_wait(driver.find_element_by_link_text("Language Variety"))
        self.assertEqual("Castilian (7)", driver.find_element_by_xpath(
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
        self.assertEqual("Tool/Service", driver.find_element_by_xpath(
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
        self.assertEqual("10 Language Resources", driver.find_element_by_css_selector("h3").text)
        # additionally filter by license
        driver.find_element_by_link_text("Licence").click()
        driver.find_element_by_link_text("ELRA_VAR").click()
        self.assertEqual("6 Language Resources", driver.find_element_by_css_selector("h3").text)
        # additionally filter by media type
        driver.find_element_by_link_text("Media Type").click()
        driver.find_element_by_link_text("Text").click()
        self.assertEqual("5 Language Resources", driver.find_element_by_css_selector("h3").text)
        # additionally filter by restriction of use
        driver.find_element_by_link_text("Restrictions of Use").click()
        driver.find_element_by_link_text("Commercial Use").click()
        self.assertEqual("5 Language Resources", driver.find_element_by_css_selector("h3").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))
        # remove language filter
        driver.find_element_by_link_text("English").click()
        self.assertEqual("10 Language Resources", driver.find_element_by_css_selector("h3").text)
        # remove license filter
        driver.find_element_by_link_text("ELRA_VAR").click()
        self.assertEqual("10 Language Resources", driver.find_element_by_css_selector("h3").text)
        # remove media type filter
        driver.find_element_by_link_text("Text").click()
        self.assertEqual("15 Language Resources", driver.find_element_by_css_selector("h3").text)
        # remove restiriction of use filter
        driver.find_element_by_link_text("Commercial Use").click()
        self.assertEqual("29 Language Resources (Page 1 of 2)", driver.find_element_by_css_selector("h3").text)
        driver.get_screenshot_as_file('{0}/{1}.png'.format(ss_path, time.time()))

        # Test sub filters
        # Test all sub filter of Resource Type / Corpus are available
        click_and_wait(driver.find_element_by_link_text("Resource Type"))
        click_and_wait(driver.find_element_by_link_text("Corpus"))
        self.assertEqual("Annotation Type", driver.find_element_by_link_text("Annotation Type").text)
        self.assertEqual("Annotation Format", driver.find_element_by_link_text("Annotation Format").text)
        # check content of Annotation Type filter
        click_and_wait(driver.find_element_by_link_text("Annotation Type"))
        self.assertEqual("Segmentation (4)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[1]").text)
        self.assertEqual("Lemmatization (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[2]").text)
        self.assertEqual("Modality Annotation - Body Movements (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[3]").text)
        self.assertEqual("Morphosyntactic Annotation - B Pos Tagging (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[4]").text)
        self.assertEqual("Morphosyntactic Annotation - Pos Tagging (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[5]").text)
        self.assertEqual("more", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[16]").text)
        # check Corpus filter more/less
        click_and_wait(driver.find_element_by_link_text("more"))
        self.assertEqual("Other (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[6]").text)
        self.assertEqual("Semantic Annotation - Named Entities (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[7]").text)
        self.assertEqual("Structural Annotation (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[8]").text)
        self.assertEqual("Alignment (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[9]").text)
        self.assertEqual("Modality Annotation - Facial Expressions (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[10]").text)
        self.assertEqual("Modality Annotation - Hand Arm Gestures (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[11]").text)
        self.assertEqual("Speech Annotation (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[12]").text)
        self.assertEqual("Speech Annotation - Orthographic Transcription (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[13]").text)
        self.assertEqual("Speech Annotation - Phonetic Transcription (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[14]").text)
        self.assertEqual("Syntactic Annotation - Shallow Parsing (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[15]").text)
        self.assertEqual("less", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[16]").text)
        click_and_wait(driver.find_element_by_link_text("less"))
        self.assertEqual("more", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[16]").text)
        # Close Annotation Type filter
        click_and_wait(driver.find_element_by_link_text("Annotation Type"))
        # check content of Annotation Format filter
        click_and_wait(driver.find_element_by_link_text("Annotation Format"))
        self.assertEqual("Text/xml (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[1]").text)
        self.assertEqual("TIPSTER (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[2]").text)
        self.assertEqual("XML (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[3]").text)
        self.assertEqual("Eaf (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[4]").text)
        self.assertEqual("Trs (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[5]").text)
        # Close Annotation Type filter
        click_and_wait(driver.find_element_by_link_text("Annotation Format"))
        # remove Resource Type filter
        click_and_wait(driver.find_element_by_link_text("Corpus"))
       
        # Test all sub filter of Resource Type / Lexical Conceptual Resource are available
        click_and_wait(driver.find_element_by_link_text("Resource Type"))
        click_and_wait(driver.find_element_by_link_text("Lexical Conceptual Resource"))
        self.assertEqual("Lexical/Conceptual Resource Type", driver.find_element_by_link_text("Lexical/Conceptual Resource Type").text)
        self.assertEqual("Encoding Level", driver.find_element_by_link_text("Encoding Level").text)
        self.assertEqual("Linguistic Information", driver.find_element_by_link_text("Linguistic Information").text)
        # check content of Lexical/Conceptual Resource Type filter
        click_and_wait(driver.find_element_by_link_text("Lexical/Conceptual Resource Type"))
        self.assertEqual("Lexicon (6)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[1]").text)
        self.assertEqual("Terminological Resource (4)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[2]").text)
        self.assertEqual("Computational Lexicon (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[3]").text)
        # Close Lexical/Conceptual Resource Type filter
        click_and_wait(driver.find_element_by_link_text("Lexical/Conceptual Resource Type"))
        # check content of Encoding Level filter
        click_and_wait(driver.find_element_by_link_text("Encoding Level"))
        self.assertEqual("Morphology (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[1]").text)
        self.assertEqual("Semantics (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[2]").text)
        self.assertEqual("Syntax (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[3]").text)
        # Close Encoding Level filter
        click_and_wait(driver.find_element_by_link_text("Encoding Level"))
        # check content of Linguistic Information filter
        click_and_wait(driver.find_element_by_link_text("Linguistic Information"))
        self.assertEqual("Definition/gloss (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[7]/div[1]").text)
        self.assertEqual("Part Of Speech (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[7]/div[2]").text)
        self.assertEqual("Semantics - Event Type (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[7]/div[3]").text)
        self.assertEqual("Semantics - Semantic Roles (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[7]/div[4]").text)
        # Close Linguistic Information filter
        click_and_wait(driver.find_element_by_link_text("Linguistic Information"))
        # remove Resource Type filter
        click_and_wait(driver.find_element_by_link_text("Lexical Conceptual Resource"))
        
        # Test all sub filter of Resource Type / Tool Service are available
        click_and_wait(driver.find_element_by_link_text("Resource Type"))
        click_and_wait(driver.find_element_by_link_text("Tool Service"))
        self.assertEqual("Tool/Service Type", driver.find_element_by_link_text("Tool/Service Type").text)
        self.assertEqual("Tool/Service Subtype", driver.find_element_by_link_text("Tool/Service Subtype").text)
        self.assertEqual("Language Dependent", driver.find_element_by_link_text("Language Dependent").text)
        self.assertEqual("InputInfo/OutputInfo Resource Type", driver.find_element_by_link_text("InputInfo/OutputInfo Resource Type").text)
        self.assertEqual("InputInfo/OutputInfo Media Type", driver.find_element_by_link_text("InputInfo/OutputInfo Media Type").text)
        self.assertEqual("Annotation Type", driver.find_element_by_link_text("Annotation Type").text)
        self.assertEqual("Annotation Format", driver.find_element_by_link_text("Annotation Format").text)
        self.assertEqual("Evaluated", driver.find_element_by_link_text("Evaluated").text)
        # check content of Tool/Service Type filter
        click_and_wait(driver.find_element_by_link_text("Tool/Service Type"))
        self.assertEqual("Platform (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[1]").text)
        self.assertEqual("Service (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[2]").text)
        self.assertEqual("Tool (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[3]").text)
        # Close Tool/Service Type filter
        click_and_wait(driver.find_element_by_link_text("Tool/Service Type"))
        # check content of Tool/Service Subtype filter
        click_and_wait(driver.find_element_by_link_text("Tool/Service Subtype"))
        self.assertEqual("Text- To- Speech server (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[1]").text)
        self.assertEqual("Soap-service (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[2]").text)
        # Close Tool/Service Subtype filter
        click_and_wait(driver.find_element_by_link_text("Tool/Service Subtype"))
        # check content of Language Dependent filter
        click_and_wait(driver.find_element_by_link_text("Language Dependent"))
        self.assertEqual("No (2)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[7]/div[1]").text)
        self.assertEqual("Yes (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[7]/div[2]").text)
        # Close Language Dependent filter
        click_and_wait(driver.find_element_by_link_text("Language Dependent"))
        # check content of InputInfo/OutputInfo Resource Type filter
        click_and_wait(driver.find_element_by_link_text("InputInfo/OutputInfo Resource Type"))
        self.assertEqual("Corpus (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[9]/div[1]").text)
        self.assertEqual("Language Description (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[9]/div[2]").text)
        self.assertEqual("Lexical Conceptual Resource (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[9]/div[3]").text)
        # Close InputInfo/OutputInfo Resource Type filter
        click_and_wait(driver.find_element_by_link_text("InputInfo/OutputInfo Resource Type"))
        # check content of InputInfo/OutputInfo Media Type filter
        click_and_wait(driver.find_element_by_link_text("InputInfo/OutputInfo Media Type"))
        self.assertEqual("Text (3)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[11]/div[1]").text)
        self.assertEqual("Audio (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[11]/div[2]").text)
        # Close InputInfo/OutputInfo Media Type filter
        click_and_wait(driver.find_element_by_link_text("InputInfo/OutputInfo Media Type"))
        # check content of Annotation Type filter
        click_and_wait(driver.find_element_by_link_text("Annotation Type"))
        self.assertEqual("Morphosyntactic Annotation - Pos Tagging (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[13]/div[1]").text)
        # Close Annotation Type filter
        click_and_wait(driver.find_element_by_link_text("Annotation Type"))
        # check content of Annotation Format filter
        click_and_wait(driver.find_element_by_link_text("Annotation Format"))
        self.assertEqual("Plain text (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[15]/div[1]").text)
        self.assertEqual("Tab separated (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[15]/div[2]").text)
        # Close Annotation Format filter
        click_and_wait(driver.find_element_by_link_text("Annotation Format"))
        # check content of Evaluated filter
        click_and_wait(driver.find_element_by_link_text("Evaluated"))
        self.assertEqual("Yes (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[17]/div[1]").text)
        # Close Evaluated filter
        click_and_wait(driver.find_element_by_link_text("Evaluated"))
        # remove Resource Type filter
        click_and_wait(driver.find_element_by_link_text("Tool Service"))

        # Test all sub filter of Media Type / Text are available
        click_and_wait(driver.find_element_by_link_text("Media Type"))
        click_and_wait(driver.find_element_by_link_text("Text"))
        self.assertEqual("Text Genre", driver.find_element_by_link_text("Text Genre").text)
        self.assertEqual("Text Type", driver.find_element_by_link_text("Text Type").text)
        self.assertEqual("Register", driver.find_element_by_link_text("Register").text)
        # check content of Text Genre filter
        click_and_wait(driver.find_element_by_link_text("Text Genre"))
        self.assertEqual("Advertising (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[1]").text)
        self.assertEqual("Discussion (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[2]").text)
        self.assertEqual("Feature (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[3]").text)
        self.assertEqual("Fiction (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[4]").text)
        self.assertEqual("Information (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[5]").text)
        self.assertEqual("more", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[10]").text)
        # check Text Genre filter more/less
        click_and_wait(driver.find_element_by_link_text("more"))
        self.assertEqual("Interviews (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[6]").text)
        self.assertEqual("Non-fiction (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[7]").text)
        self.assertEqual("Official (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[8]").text)
        self.assertEqual("Private (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[9]").text)
        self.assertEqual("less", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[10]").text)
        click_and_wait(driver.find_element_by_link_text("less"))
        self.assertEqual("more", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[10]").text)
        # Close Text Genre filter
        click_and_wait(driver.find_element_by_link_text("Text Genre"))
        # check content of Text Type filter
        click_and_wait(driver.find_element_by_link_text("Text Type"))
        self.assertEqual("Fairy tales (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[1]").text)
        self.assertEqual("Fiction (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[2]").text)
        self.assertEqual("Poems (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[3]").text)
        self.assertEqual("Quasi-spoken (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[4]").text)
        # Close Text Type filter
        click_and_wait(driver.find_element_by_link_text("Text Type"))
        # check content of Register filter
        # with xpath because Register send to the Account Registration
        click_and_wait(driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[6]/a"))
        self.assertEqual("Formal (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[7]/div[1]").text)
        # Close Register filter
        click_and_wait(driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[6]/a"))
        click_and_wait(driver.find_element_by_link_text("Text"))
       
        # Test all sub filter of Media Type / Audio are available
        click_and_wait(driver.find_element_by_link_text("Media Type"))
        click_and_wait(driver.find_element_by_link_text("Audio"))
        self.assertEqual("Audio Genre", driver.find_element_by_link_text("Audio Genre").text)
        self.assertEqual("Speech Genre", driver.find_element_by_link_text("Speech Genre").text)
        self.assertEqual("Speech Items", driver.find_element_by_link_text("Speech Items").text)
        self.assertEqual("Naturality", driver.find_element_by_link_text("Naturality").text)
        self.assertEqual("Conversational Type", driver.find_element_by_link_text("Conversational Type").text)
        self.assertEqual("Scenario Type", driver.find_element_by_link_text("Scenario Type").text)
        # check content of Audio Genre filter
        click_and_wait(driver.find_element_by_link_text("Audio Genre"))
        self.assertEqual("Speech (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[1]").text)
        # Close Audio Genre filter
        click_and_wait(driver.find_element_by_link_text("Audio Genre"))
        # check content of Speech Genre filter
        click_and_wait(driver.find_element_by_link_text("Speech Genre"))
        self.assertEqual("Interview (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[1]").text)
        # Close Speech Genre filter
        click_and_wait(driver.find_element_by_link_text("Speech Genre"))
        # check content of Speech Items filter
        click_and_wait(driver.find_element_by_link_text("Speech Items"))
        self.assertEqual("Free Speech (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[7]/div[1]").text)
        # Close Speech Items filter
        click_and_wait(driver.find_element_by_link_text("Speech Items"))
        # check content of Naturality filter
        click_and_wait(driver.find_element_by_link_text("Naturality"))
        self.assertEqual("Natural (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[9]/div[1]").text)
        # Close Naturality filter
        click_and_wait(driver.find_element_by_link_text("Naturality"))
        # check content of Conversational Type filter
        click_and_wait(driver.find_element_by_link_text("Conversational Type"))
        self.assertEqual("Dialogue (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[11]/div[1]").text)
        # Close Conversational Type filter
        click_and_wait(driver.find_element_by_link_text("Conversational Type"))
        # check content of Scenario Type filter
        click_and_wait(driver.find_element_by_link_text("Scenario Type"))
        self.assertEqual("Other (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[13]/div[1]").text)
        # Close Scenario Type filter
        click_and_wait(driver.find_element_by_link_text("Scenario Type"))
        # remove Media Type filter
        click_and_wait(driver.find_element_by_link_text("Audio"))
       
        # Test all sub filter of Media Type / Video are available
        click_and_wait(driver.find_element_by_link_text("Media Type"))
        click_and_wait(driver.find_element_by_link_text("Video"))
        self.assertEqual("Video Genre", driver.find_element_by_link_text("Video Genre").text)
        self.assertEqual("Type of Video Content", driver.find_element_by_link_text("Type of Video Content").text)
        self.assertEqual("Naturality", driver.find_element_by_link_text("Naturality").text)
        self.assertEqual("Conversational Type", driver.find_element_by_link_text("Conversational Type").text)
        self.assertEqual("Scenario Type", driver.find_element_by_link_text("Scenario Type").text)
        # check content of Video Genre filter
        click_and_wait(driver.find_element_by_link_text("Video Genre"))
        self.assertEqual("Interview (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[3]/div[1]").text)
        # Close Video Genre filter
        click_and_wait(driver.find_element_by_link_text("Video Genre"))
        # check content of Type of Video Content filter
        click_and_wait(driver.find_element_by_link_text("Type of Video Content"))
        self.assertEqual("11 face to face TV interviews (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[5]/div[1]").text)
        # Close Type of Video Content filter
        click_and_wait(driver.find_element_by_link_text("Type of Video Content"))
        # check content of Naturality filter
        click_and_wait(driver.find_element_by_link_text("Naturality"))
        self.assertEqual("Natural (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[7]/div[1]").text)
        # Close Naturality filter
        click_and_wait(driver.find_element_by_link_text("Naturality"))
        # check content of Conversational Type filter
        click_and_wait(driver.find_element_by_link_text("Conversational Type"))
        self.assertEqual("Dialogue (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[9]/div[1]").text)
        # Close Conversational Type filter
        click_and_wait(driver.find_element_by_link_text("Conversational Type"))
        # check content of Scenario Type filter
        click_and_wait(driver.find_element_by_link_text("Scenario Type"))
        self.assertEqual("Other (1)", driver.find_element_by_xpath(
          "//div[@id='searchFilters']/div[@class='filter']/div[11]/div[1]").text)
        # Close Scenario Type filter
        click_and_wait(driver.find_element_by_link_text("Scenario Type"))
        # remove Media Type filter
        click_and_wait(driver.find_element_by_link_text("Video"))
       

