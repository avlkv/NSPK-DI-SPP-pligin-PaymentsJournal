from selenium import webdriver

from logging import config

config.fileConfig('dev.logger.conf')
from PaymentsJournal import PaymentsJournal

driver = webdriver.Chrome()

parser = PaymentsJournal(driver)
docs = parser.content()

print(*docs, sep='\n\r\n')
