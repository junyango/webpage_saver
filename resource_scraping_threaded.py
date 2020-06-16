from warnings import simplefilter 
simplefilter(action='ignore', category=FutureWarning)

from multiprocessing import Process, Queue

# Multi-threading packages
from threading import Thread
import threading
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

# Implementing a global lock to fix multi-threading deadlock issue
lock = threading.Lock()

# Returns a list, filtering empty spaces
def initialize_list(path):
	item_list = []
	with open(path, "r") as f:
		content = f.readlines()
		for line in content:
			file_name = line.split("\t")[0].strip()
			url = line.split("\t")[1].strip()
			ground_truth = line.split("\t")[2].strip()
			item_list.append((file_name, url, ground_truth))

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


# This part is used for collective multi-threaded (wary of GIL) testing
# Creating a class for each worker thread
# Instantiating one driver per thread only once to reduce overhead
class Worker(Thread):
	def __init__(self, queue, output_dir):
		Thread.__init__(self)
		self.queue = queue
		self.output_dir = output_dir

		# Initializing pywebcopy settings
		self.kwargs = {'bypass_robots': True, 'zip_project_folder': False, 'join_timeout':5}

		# Initializing chrome driver settings to run headless, windows resolution etc.
		chrome_driver_options = initialize_chrome_settings()
		chromedriver = main_config.chromedriver
		try:
			print("Starting driver!")
			self.driver = webdriver.Chrome(chromedriver, options=chrome_driver_options)
			self.driver.set_page_load_timeout(60)
			self.driver.set_script_timeout(60)
			print("Session is created!")
		except SessionNotCreatedException as snce:
			print("Session not Created!")
			return

	def run(self):
		while True:
			# Get the work from the queue and expand the tuple
			item = self.queue.get()
			try:
				file_name, url, brand = item
				print("Testing: " + url + " now!")
				output_path = os.path.join(self.output_dir, file_name)
				# Extracts screenshot, html.txt and url.txt into an output folder
				#  Output: html.txt, coordinates.txt, shot.png, info.txt that stores URL
				# Coordinates are extracted via HTML and CSS heuristics
				url, url_redirected, output_folder = screenshot_crawler.main(link, self.driver, output_path)
				# Pipeline output from screenshot crawler (url, and output_folder) to save_webpage to save entire webpage locally 
				if url_redirected is not None and output_folder is not None:
					try:
						save_webpage(url_redirected, output_folder, **self.kwargs)
					except Exception:
						pass
			except Exception:
				pass
			finally:
				self.queue.task_done()

def main(links, output_dir):
	# Create a queue to communicate with the worker threads
	queue = Queue()
    # Create 5 worker threads
	for x in range(5):
		worker = Worker(queue, output_dir)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.setDaemon(True)
		worker.start()
	# Put the tasks into the queue as a tuple
	for link in links:
		queue.put(link)

	# Causes the main thread to wait for the queue to finish processing all the tasks
	queue.join()

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', "--file", help='Input file path to parse', required=True)
	args = parser.parse_args()

	output_dir = main_config.output
		
	# Getting list of URLs to crawl
	file_to_crawl = args.file
	links = initialize_list(file_to_crawl)

	main(links, output_dir)


