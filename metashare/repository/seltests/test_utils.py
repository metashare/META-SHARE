"""
Utility functions for Selenium unit tests.
"""
from metashare.settings import ROOT_PATH, TEST_MODE_NAME
import os
from metashare import test_utils
import time
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.alert import Alert

def login_user(driver, user_name, user_passwd):
    """
    logs in given user;
    assumes that the browser is at the top level META-SHARE page
    """
    # TODO remove this workaround when Selenium starts working again as intended
    driver.set_window_size(1280, 1024)
    driver.find_element_by_xpath("//div[@id='inner']/div[2]/a[2]/div").click()
    driver.find_element_by_id("id_username").clear()
    driver.find_element_by_id("id_username").send_keys(user_name)
    driver.find_element_by_id("id_password").clear()
    driver.find_element_by_id("id_password").send_keys(user_passwd)
    driver.find_element_by_css_selector("input.button.middle_button").click()

def mouse_over(driver, web_ele):
    """
    simulates mouse over the given web element
    """
    code = "var fireOnThis = arguments[0]; " + \
      "var evObj = document.createEvent('MouseEvents'); " + \
      "evObj.initEvent( 'mouseover', true, true ); " + \
      "fireOnThis.dispatchEvent(evObj);"
    driver.execute_script(code, web_ele)


def click_menu_item(driver, web_ele):
    """
    Simulates a click on the given web element which must have an attribute 
    'href'. The click is simulated by just following the link.
    """
    driver.get(web_ele.get_attribute("href")) 

def save_and_close(driver, target_id):
    """
    Clicks the save button in the current window, waits until it is closed and
    then changes to the window with the given target id.
    is closed.
    """
    current_id = driver.current_window_handle
    driver.find_element_by_name("_save").click()
    try:
        while driver.switch_to_window(current_id):
            time.sleep(1)
    except NoSuchWindowException:
        pass
    # TODO remove this workaround when Selenium starts working again as intended
    time.sleep(1)
    driver.switch_to_window(target_id)

def cancel_and_close(driver, target_id):
    """
    Clicks the cancel button in the current window, waits until it is closed and
    then changes to the window with the given target id.
    is closed.
    """
    current_id = driver.current_window_handle
    driver.find_element_by_name("_cancel").click()
    alert = driver.switch_to_alert()
    alert.accept()
    
    try:
        while driver.switch_to_window(current_id):
            time.sleep(1)
    except NoSuchWindowException:
        pass
    # TODO remove this workaround when Selenium starts working again as intended
    time.sleep(1)
    driver.switch_to_window(target_id)

def click_and_wait(web_ele):
    """
    Clicks the given web element and waits 1 second.
    """
    web_ele.click()
    # TODO remove this workaround when Selenium starts working again as intended
    time.sleep(1)
    
def setup_screenshots_folder(test_class, test_method):
    """
    prepares a folder for screenshots for the given test
    """
    ss_path = '{0}/reports/{1}/{2}'.format(ROOT_PATH, test_class, test_method)
    if not os.path.exists(ss_path):
        os.makedirs(ss_path)
    for one_file in os.listdir(ss_path):
        file_path = os.path.join(ss_path, one_file)
        os.unlink(file_path)
    return ss_path


def import_dir(path):
    """
    imports all XML files in the given directory
    """
    # to speed up the import, we disable indexing during the import and only
    # rebuild the index at afterwards
    os.environ['DISABLE_INDEXING_DURING_IMPORT'] = 'True'
    _files = os.listdir(path)
    for _file in _files:
        test_utils.import_xml_or_zip("%s%s" % (path, _file))
    os.environ['DISABLE_INDEXING_DURING_IMPORT'] = 'False'
    from django.core.management import call_command
    call_command('rebuild_index', interactive=False, using=TEST_MODE_NAME)
