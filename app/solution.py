import random
from typing import List, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
import time
from loguru import logger
from app.captcha_resolver import CaptchaResolver
from app.settings import CAPTCHA_ENTIRE_IMAGE_FILE_PATH, CAPTCHA_SINGLE_IMAGE_FILE_PATH
from app.utils import get_question_id_by_target_name, resize_base64_image


class Solution(object):
    def __init__(self, url):
        self.browser = webdriver.Chrome()
        self.browser.get(url)
        self.wait = WebDriverWait(self.browser, 10)
        self.captcha_rectangles_number = None
        self.entire_captcha_width = None
        self.captcha_resolver = CaptchaResolver()

    def __del__(self):
        time.sleep(10)
        self.browser.close()

    def get_all_frames(self) -> List[WebElement]:
        self.browser.switch_to.default_content()
        return self.browser.find_elements_by_tag_name('iframe')

    def get_captcha_entry_iframe(self) -> WebElement:
        self.browser.switch_to.default_content()
        captcha_entry_iframe = self.browser.find_element_by_css_selector(
            'iframe[title="reCAPTCHA"]')
        return captcha_entry_iframe

    def switch_to_captcha_entry_iframe(self) -> None:
        captcha_entry_iframe: WebElement = self.get_captcha_entry_iframe()
        self.browser.switch_to.frame(captcha_entry_iframe)

    def get_captcha_content_iframe(self) -> WebElement:
        self.browser.switch_to.default_content()
        captcha_content_iframe = self.browser.find_element_by_xpath(
            '//iframe[contains(@title, "recaptcha challenge")]')
        return captcha_content_iframe

    def switch_to_captcha_content_iframe(self) -> None:
        captcha_content_iframe: WebElement = self.get_captcha_content_iframe()
        self.browser.switch_to.frame(captcha_content_iframe)

    def get_entire_captcha_element(self) -> WebElement:
        entire_captcha_element: WebElement = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#rc-imageselect-target')))
        return entire_captcha_element

    def get_entire_captcha_natural_width(self) -> Union[int, None]:
        result = self.browser.execute_script(
            "return document.querySelector('div.rc-image-tile-wrapper > img').naturalWidth")
        if result:
            return int(result)
        return None

    def get_entire_captcha_display_width(self) -> Union[int, None]:
        entire_captcha_element = self.get_entire_captcha_element()
        if entire_captcha_element:
            return entire_captcha_element.rect.get('width')
        return None

    def trigger_captcha(self) -> None:
        self.switch_to_captcha_entry_iframe()
        captcha_entry = self.wait.until(EC.presence_of_element_located(
            (By.ID, 'recaptcha-anchor')))
        captcha_entry.click()
        time.sleep(2)
        self.switch_to_captcha_content_iframe()
        entire_captcha_element: WebElement = self.get_entire_captcha_element()
        if entire_captcha_element.is_displayed:
            logger.debug('trigged captcha successfully')

    def get_captcha_target_name(self) -> WebElement:
        captcha_target_name_element: WebElement = self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '.rc-imageselect-desc-wrapper strong')))
        return captcha_target_name_element.text

    def get_verify_button(self) -> WebElement:
        verify_button = self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#recaptcha-verify-button')))
        return verify_button

    def verify_single_captcha(self, index):
        time.sleep(3)
        elements = self.wait.until(EC.visibility_of_all_elements_located(
            (By.CSS_SELECTOR, '#rc-imageselect-target table td')))
        single_captcha_element: WebElement = elements[index]
        class_name = single_captcha_element.get_attribute('class')
        logger.debug(f'verifiying single captcha {index}, class {class_name}')
        if 'selected' in class_name:
            logger.debug(f'no new single captcha displayed')
            return
        logger.debug('new single captcha displayed')
        single_captcha_element.screenshot(CAPTCHA_SINGLE_IMAGE_FILE_PATH)
        resized_single_captcha_base64_string = resize_base64_image(
            CAPTCHA_SINGLE_IMAGE_FILE_PATH, (100, 100))
        single_captcha_recognize_result = self.captcha_resolver.create_task(
            resized_single_captcha_base64_string, get_question_id_by_target_name(self.captcha_target_name))
        if not single_captcha_recognize_result:
            logger.error('count not get single captcha recognize result')
            return
        has_object = single_captcha_recognize_result.get(
            'solution', {}).get('hasObject')
        if has_object is None:
            logger.error('count not get captcha recognized indices')
            return
        if has_object is False:
            logger.debug('no more object in this single captcha')
            return
        if has_object:
            single_captcha_element.click()
            # check for new single captcha
            self.verify_single_captcha(index)

    def get_verify_error_info(self):
        self.switch_to_captcha_content_iframe()
        self.browser.execute_script(
            "return document.querySelector('div.rc-imageselect-incorrect-response')?.text")

    def get_is_successful(self):
        self.switch_to_captcha_entry_iframe()
        anchor: WebElement = self.wait.until(EC.visibility_of_element_located((
            By.ID, 'recaptcha-anchor'
        )))
        checked = anchor.get_attribute('aria-checked')
        logger.debug(f'checked {checked}')
        return str(checked) == 'true'

    def get_is_failed(self):
        return bool(self.get_verify_error_info())

    def verify_entire_captcha(self):
        captcha_rectangles = self.wait.until(EC.visibility_of_all_elements_located(
            (By.CSS_SELECTOR, '#rc-imageselect-target table td')))
        self.captcha_rectangles_number = len(captcha_rectangles)
        logger.debug(
            f'captcha_rectangles_number {self.captcha_rectangles_number}')
        captcha_lines = self.wait.until(EC.visibility_of_all_elements_located(
            (By.CSS_SELECTOR, '#rc-imageselect-target table tr')))
        self.captcha_row_number = len(captcha_lines)
        self.captcha_col_number = self.captcha_row_number
        logger.debug(
            f'captcha_row_number {self.captcha_row_number} captcha_col_number {self.captcha_col_number}')
        self.entire_captcha_natural_width = self.get_entire_captcha_natural_width()
        logger.debug(
            f'entire_captcha_natural_width {self.entire_captcha_natural_width}'
        )
        self.entire_captcha_display_width = self.get_entire_captcha_display_width()
        self.entire_captcha_display_height = self.entire_captcha_display_width
        logger.debug(
            f'entire_captcha_display_width {self.entire_captcha_display_width}'
        )
        self.captcha_target_name = self.get_captcha_target_name()
        logger.debug(
            f'captcha_target_name {self.captcha_target_name}'
        )
        entire_captcha_element: WebElement = self.get_entire_captcha_element()
        entire_captcha_element.screenshot(
            CAPTCHA_ENTIRE_IMAGE_FILE_PATH)
        logger.debug(
            f'saved entire captcha to {CAPTCHA_ENTIRE_IMAGE_FILE_PATH}')
        resized_entire_captcha_base64_string = resize_base64_image(
            CAPTCHA_ENTIRE_IMAGE_FILE_PATH, (self.entire_captcha_natural_width,
                                             self.entire_captcha_natural_width))
        logger.debug(
            f'resized_entire_captcha_base64_string, {resized_entire_captcha_base64_string[0:100]}...')
        entire_captcha_recognize_result = self.captcha_resolver.create_task(
            resized_entire_captcha_base64_string,
            get_question_id_by_target_name(self.captcha_target_name)
        )
        if not entire_captcha_recognize_result:
            logger.error('count not get captcha recognize result')
            return
        recognized_indices = entire_captcha_recognize_result.get(
            'solution', {}).get('objects')
        if not recognized_indices:
            logger.error('count not get captcha recognized indices')
            return
        for recognized_index in recognized_indices:
            offset_x = recognized_index % self.captcha_row_number * \
                (self.entire_captcha_display_width / self.captcha_row_number) + \
                random.randint(
                    0, int(self.entire_captcha_display_width / self.captcha_row_number))
            offset_y = recognized_index // self.captcha_col_number * \
                (self.entire_captcha_display_height / self.captcha_col_number) + \
                random.randint(
                    0, int(self.entire_captcha_display_height / self.captcha_col_number))
            logger.debug(
                f'recognized_index {recognized_index} click offset {offset_x}, {offset_y}')
            # click target
            ac = ActionChains(self.browser)
            ac.move_to_element(entire_captcha_element) \
                .move_by_offset(-self.entire_captcha_display_width / 2, -self.entire_captcha_display_height / 2) \
                .move_by_offset(
                offset_x, offset_y).click().perform()
            # check if need verify single captcha
            self.verify_single_captcha(recognized_index)

        # after all captcha clicked
        verify_button: WebElement = self.get_verify_button()
        if verify_button.is_displayed:
            verify_button.click()
            time.sleep(3)

        is_succeed = self.get_is_successful()
        if is_succeed:
            logger.debug('verifed successfully')
        else:
            verify_error_info = self.get_verify_error_info()
            logger.debug(f'verify_error_info {verify_error_info}')
            self.verify_entire_captcha()

    def resolve(self):
        self.trigger_captcha()
        self.verify_entire_captcha()