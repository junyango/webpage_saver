from warnings import simplefilter 
simplefilter(action='ignore', category=FutureWarning)

from queue import Queue
import logging
import main_config

# Selenium packages
from selenium import webdriver
from selenium.common.exceptions import *

# pywebcopy scrape webpage
from pywebcopy import config
from pywebcopy import save_webpage

import screenshot_crawler
import os

import argparse

# Returns a list, filtering empty spaces
def initialize_list(path):
	item_list = []
	with open(path, "r") as f:
		content = f.readlines()
		for line in content:
			url = line.split("\t")[0].strip()
			ground_truth = line.split("\t")[1].strip()
			item_list.append((url, ground_truth))

	return item_list


# --start-maximized may not work so well because headless does not recognize resolution size
# therefore, windowsize has to be explicitly specified
def initialize_chrome_settings():
	options = webdriver.ChromeOptions()
	options.add_argument('--ignore-certificate-errors')
	options.add_argument('--ignore-certificate-errors-spki-list')
	options.add_argument('--ignore-ssl-errors')
	options.add_argument("--start-maximized")
	options.add_argument("--headless")
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument("--window-size=1920,1080")
	options.add_argument("--enable-javascript")
	options.add_argument("--disable-gpu")

	return options


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', "--file", help='Input file path to parse', required=True)
	args = parser.parse_args()

	output_dir = main_config.output
		
	# Getting list of URLs to crawl
	file_to_crawl = args.file
	links = initialize_list(file_to_crawl)

	# Initializing chrome driver settings to run headless, windows resolution etc.
	chrome_driver_options = initialize_chrome_settings()
	chromedriver = main_config.chromedriver
	try:
		print("Starting driver!")
		driver = webdriver.Chrome(chromedriver, options=chrome_driver_options)
		driver.set_page_load_timeout(60)
		driver.set_script_timeout(60)
		print("Session is created!")
	except SessionNotCreatedException as snce:
		print("Session not Created!")

	for item in links:
		url, brand = item
		screenshot_crawler.main(url, driver, output_dir)



	


