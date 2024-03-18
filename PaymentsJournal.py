"""
Парсер плагина SPP

1/2 документ плагина
"""
import logging
import os
import time

import dateparser
from selenium.webdriver.common.by import By

from src.spp.types import SPP_document


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

    def __init__(self, driver, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []
        self.driver = driver

        # Логер должен подключаться так. Вся настройка лежит на платформе
        self.logger = logging.getLogger(self.__class__.__name__)

        # УДалить DRAFT
        logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        self.logger.addHandler(consoleHandler)
        #

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
        self._parse()
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

        self.driver.get(
            "https://www.paymentsjournal.com/news/")  # Открыть первую страницу с материалами EMVCo в браузере
        time.sleep(10)

        # Cooskies
        try:
            cookies_btn = self.driver.find_element(By.ID, 'normal-slidedown').find_element(By.XPATH,
                                                                                           '//*[@id="onesignal-slidedown-allow-button"]')
            self.driver.execute_script('arguments[0].click()', cookies_btn)
            self.logger.info('Cookies убран')
        except:
            self.logger.exception('Не найден cookies')
            pass

        self.logger.info('Прекращен поиск Cookies')
        time.sleep(3)

        # try:
        # Get scroll height
        #    last_height = self.driver.execute_script("return document.body.scrollHeight")

        #    while True:
        # Scroll down to bottom
        #        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        #        time.sleep(0.5)

        # Calculate new scroll height and compare with last scroll height
        #        new_height = self.driver.execute_script("return document.body.scrollHeight")
        #        if new_height == last_height:
        #            break
        #        last_height = new_height

        #        try:
        #            reg_btn = self.driver.find_element(By.CLASS_NAME, 'dialog-widget-content').find_element(
        #                By.XPATH,
        #                '//*[@id="elementor-popup-modal-433761"]/div/a')
        #            self.driver.execute_script('arguments[0].click()', reg_btn)
        #            self.logger.info('Окно регистрации убрано')
        #        except:
        #            self.logger.exception('Не найдено окно регистрации')
        #            pass

        #        self.logger.info('Прекращен поиск окна регистрации')
        #        time.sleep(3)

        # except Exception as e:
        #    self.logger.exception('Не удалось найти scroll')

        flag = True
        while flag:
            self.driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
            self.logger.debug('Загрузка списка элементов...')
            doc_table = self.driver.find_element(By.CLASS_NAME, 'jeg_posts ').find_elements(By.TAG_NAME,
                                                                                            'article')
            self.logger.debug(f'Обработка списка элементов ({len(doc_table)})...')

            # Цикл по всем строкам таблицы элементов на текущей странице
            for element in doc_table:

                element_locked = False

                try:
                    title = element.find_element(By.CLASS_NAME, 'jeg_post_title').text
                    # title = element.find_element(By.XPATH, '//*[@id="feed-item-title-1"]/a').text

                except:
                    self.logger.exception('Не удалось извлечь title')
                    title = ' '

                try:
                    other_data = element.find_element(By.CLASS_NAME, "by").text
                except:
                    self.logger.exception('Не удалось извлечь other_data')
                    other_data = ''
                try:
                    date = dateparser.parse(element.find_element(By.CLASS_NAME, 'jeg_meta_date').text)
                except:
                    self.logger.exception('Не удалось извлечь date')
                    date = ' '

                # try:
                #    date = dateparser.parse(date_text)
                # except:
                #    self.logger.exception('Не удалось извлечь date')
                #    date = None

                try:
                    # abstract = element.find_element(By.CLASS_NAME, '').text
                    abstract = ' '
                except:
                    # self.logger.exception('Не удалось извлечь abstract')
                    abstract = ' '

                book = ' '

                try:
                    web_link = element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                except:
                    self.logger.exception('Не удалось извлечь web_link')
                    web_link = None

                self._content_document.append(SPP_document(
                    doc_id=None,
                    title=title,
                    abstract=abstract,
                    text=None,
                    web_link=web_link,
                    local_link=None,
                    other_data=other_data,
                    pub_date=date,
                    load_date=None,
                ))

            counter = 0

            try:
                # Get scroll height
                last_height = self.driver.execute_script("return document.body.scrollHeight")

                while True:
                    # Scroll down to bottom
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    counter += 1
                    print(counter)

                    # Wait to load page
                    time.sleep(0.5)

                    # Calculate new scroll height and compare with last scroll height
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    if counter > 100:
                        flag = False
                        break
                    last_height = new_height

                    try:
                        reg_btn = self.driver.find_element(By.CLASS_NAME, 'dialog-widget-content').find_element(
                            By.XPATH,
                            '//*[@id="elementor-popup-modal-433761"]/div/a')
                        reg_btn.click()
                        self.logger.info('Окно регистрации убрано')
                    except:
                        # self.logger.exception('Не найдено окно регистрации')
                        pass

                    self.logger.info('Прекращен поиск окна регистрации')
                    time.sleep(3)

            except Exception as e:
                self.logger.exception('Не удалось найти scroll')
                break

            # try:
            #    pagination_arrow = self.driver.find_element(By.XPATH, '//a[contains(@data-direction,\'next\')]')
            #    self.driver.execute_script('arguments[0].click()', pagination_arrow)
            #    time.sleep(3)
            #    pg_num = self.driver.find_element(By.ID, 'current_page').text
            #    self.logger.info(f'Выполнен переход на след. страницу: {pg_num}')

            #                 if int(pg_num) > 5:
            #                     self.logger.info('Выполнен переход на 6-ую страницу. Принудительное завершение парсинга.')
            #                     break

            # try:
            #    while self.driver.find_element(By.TAG_NAME,'div'):
            #        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            #        Divs = self.driver.find_element(By.TAG_NAME,'div').text
            #        if 'End of Results' in Divs:
            #            print
            #            'end'
            #            break
            #        else:
            #            continue
            # except:
            #    self.logger.exception('Не удалось найти переход на след. страницу. Прерывание цикла обработки')
            #    break

        # Логирование найденного документа
        # self.logger.info(self._find_document_text_for_logger(_content_document))

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

    @staticmethod
    def some_necessary_method():
        """
        Если для парсинга нужен какой-то метод, то его нужно писать в классе.

        Например: конвертация дат и времени, конвертация версий документов и т. д.
        :return:
        :rtype:
        """
        ...

    @staticmethod
    def nasty_download(driver, path: str, url: str) -> str:
        """
        Метод для "противных" источников. Для разных источника он может отличаться.
        Но основной его задачей является:
            доведение driver селениума до файла непосредственно.

            Например: пройти куки, ввод форм и т. п.

        Метод скачивает документ по пути, указанному в driver, и возвращает имя файла, который был сохранен
        :param driver: WebInstallDriver, должен быть с настроенным местом скачивания
        :_type driver: WebInstallDriver
        :param url:
        :_type url:
        :return:
        :rtype:
        """

        with driver:
            driver.set_page_load_timeout(40)
            driver.get(url=url)
            time.sleep(1)

            # ========================================
            # Тут должен находится блок кода, отвечающий за конкретный источник
            # -
            # ---
            # ========================================

            # Ожидание полной загрузки файла
            while not os.path.exists(path + '/' + url.split('/')[-1]):
                time.sleep(1)

            if os.path.isfile(path + '/' + url.split('/')[-1]):
                # filename
                return url.split('/')[-1]
            else:
                return ""
