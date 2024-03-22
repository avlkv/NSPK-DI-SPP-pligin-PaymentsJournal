"""
Парсер плагина SPP

1/2 документ плагина
"""
import logging
import time

import dateparser
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from src.spp.types import SPP_document
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class PaymentsJournal:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'PaymentsJournal'

    HOST = "https://www.paymentsjournal.com/news/"
    _content_document: list[SPP_document]

    def __init__(self, webdriver: WebDriver, last_document: SPP_document = None, max_count_documents: int = 100,
                 num_scrolls: int = 25, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []

        self.driver = webdriver
        self.wait = WebDriverWait(self.driver, timeout=20)
        self.max_count_documents = max_count_documents
        self.last_document = last_document
        self.num_scrolls = num_scrolls

        # Логер должен подключаться так. Вся настройка лежит на платформе
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Parser class init completed")
        self.logger.info(f"Set source: {self.SOURCE_NAME}")
        ...

    def content(self) -> list[SPP_document]:
        """
        Главный метод парсера. Его будет вызывать платформа. Он вызывает метод _parse и возвращает список документов
        :return:
        :rtype:
        """
        self.logger.debug("Parse process start")
        try:
            self._parse()
        except Exception as e:
            self.logger.debug(f'Parsing stopped with error: {e}')
        else:
            self.logger.debug("Parse process finished")
        return self._content_document

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -

        self.driver.get(self.HOST)  # Открыть первую страницу с материалами в браузере
        time.sleep(3)

        # Cookies
        try:
            cookies_btn = self.driver.find_element(By.ID, 'normal-slidedown').find_element(By.XPATH,
                                                                                           '//*[@id="onesignal-slidedown-allow-button"]')
            self.driver.execute_script('arguments[0].click()', cookies_btn)
            self.logger.debug('Cookies убран')
        except:
            self.logger.debug('Не найден cookies')
            pass

        self.logger.debug('Прекращен поиск Cookies')
        time.sleep(3)

        flag = True
        while flag:
            self.driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
            self.logger.debug('Загрузка списка элементов...')

            counter = 0

            try:

                doc_table = self.driver.find_elements(By.TAG_NAME, 'article')
                last_doc_table_len = len(doc_table)

                while True:
                    # Scroll down to bottom
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    counter += 1
                    # self.logger.info(f"counter = {counter}")

                    # Wait to load page
                    time.sleep(1)

                    try:
                        self.driver.execute_script('arguments[0].click()', self.driver.find_element(By.XPATH,
                                                                                                    '//*[contains(@class,\'dialog-close-button\')]'))
                    except:
                        self.logger.debug('Не найдена реклама')

                    # Wait to load page
                    time.sleep(1)

                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    # Wait to load page
                    time.sleep(1)

                    doc_table = self.driver.find_elements(By.TAG_NAME, 'article')
                    new_doc_table_len = len(doc_table)
                    if last_doc_table_len == new_doc_table_len:
                        break
                    if counter > self.num_scrolls:
                        flag = False
                        break

                    try:
                        reg_btn = self.driver.find_element(By.CLASS_NAME, 'dialog-widget-content').find_element(
                            By.XPATH,
                            '//*[@id="elementor-popup-modal-433761"]/div/a')
                        reg_btn.click()
                        # self.logger.debug('Окно регистрации убрано')
                    except:
                        # self.logger.exception('Не найдено окно регистрации')
                        pass

                    # self.logger.debug('Прекращен поиск окна регистрации')
                    time.sleep(3)

            except Exception as e:
                self.logger.debug('Не удалось найти scroll')
                break

            self.logger.debug(f'Обработка списка элементов ({len(doc_table)})...')

            # Цикл по всем строкам таблицы элементов на текущей странице
            for element in doc_table:

                element_locked = False

                try:
                    title = element.find_element(By.CLASS_NAME, 'jeg_post_title').text
                    # title = element.find_element(By.XPATH, '//*[@id="feed-item-title-1"]/a').text

                except:
                    self.logger.exception('Не удалось извлечь title')
                    continue

                try:
                    web_link = element.find_element(By.CLASS_NAME, 'jeg_post_title').find_element(By.TAG_NAME,
                                                                                                  'a').get_attribute(
                        'href')
                except:
                    self.logger.exception('Не удалось извлечь web_link')
                    web_link = None

                try:
                    other_data = {
                        'author': element.find_element(By.CLASS_NAME, "jeg_meta_author").find_element(By.TAG_NAME,
                                                                                                      'a').text}
                except:
                    self.logger.debug('Не удалось извлечь other_data')
                    other_data = {}

                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[1])

                self.driver.get(web_link)
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.jeg_post_title')))

                try:
                    pub_date = dateparser.parse(self.driver.find_element(By.CLASS_NAME, 'jeg_meta_date').text)
                except:
                    self.logger.exception('Не удалось извлечь date')
                    continue

                try:
                    text_content = dateparser.parse(self.driver.find_element(By.CLASS_NAME, 'content-inner ').text)
                except:
                    self.logger.debug('Не удалось извлечь text')
                    continue

                abstract = ''

                doc = SPP_document(None,
                                   title,
                                   abstract,
                                   text_content,
                                   web_link,
                                   None,
                                   other_data,
                                   pub_date,
                                   datetime.now())

                self.find_document(doc)

                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

        # ---
        # ========================================

    @staticmethod
    def _find_document_text_for_logger(doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    def find_document(self, _doc: SPP_document):
        """
        Метод для обработки найденного документа источника
        """
        if self.last_document and self.last_document.hash == _doc.hash:
            raise Exception(f"Find already existing document ({self.last_document})")

        if self.max_count_documents and len(self._content_document) >= self.max_count_documents:
            raise Exception(f"Max count articles reached ({self.max_count_documents})")

        self._content_document.append(_doc)
        self.logger.info(self._find_document_text_for_logger(_doc))
