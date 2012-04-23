"""
Project: META-SHARE
Utility functions for Selenium unit tests.
@author: steffen
"""
from metashare.settings import ROOT_PATH
import os

def login_user(driver, user_name, user_passwd):
    """
    logs in given user;
    assumes that the browser is at the top level META-SHARE page
    """
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