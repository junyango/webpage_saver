from selenium import webdriver
import requests
import argparse
import os
from urllib.parse import urlparse
from shutil import rmtree
from selenium.common.exceptions import *
import sys
import main_config
from urllib.request import urlopen
import urllib.request
import tinycss2
import time
from bs4 import BeautifulSoup

from pywebcopy import save_webpage
import shutil
from pywebcopy import WebPage
from pywebcopy import config

import argparse


def test_link_extension(link):
	img_extensions = initialize_img_extension()
	if any(ext in link.lower() for ext in img_extensions):
		return True
	else:
		return False

# Initializing the unique file extensions
def initialize_img_extension():
	img_extensions = []
	img_extensions.append(".jpg")
	img_extensions.append(".svg")
	img_extensions.append(".png")
	img_extensions.append(".gif")
	img_extensions.append(".tiff")
	img_extensions.append(".psd")
	img_extensions.append(".ai")
	img_extensions.append(".raw")

	return img_extensions


# Method crafts into unique xpaths given a BS4 element
# Credit: https://gist.github.com/ergoithz/6cf043e3fdedd1b94fcf
def xpath_creator(element):
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:  # type: bs4.element.Tag
        siblings = parent.find_all(child.name, recursive=False)
        if len(siblings) == 1:
            if "svg" not in child.name:
                    components.append(child.name)
            else:
                # Need to handle if SVG is here
                components.append("*")

        else:
            if "svg" not in child.name:
                components.append('%s[%d]' % (child.name, next(i for i, s in enumerate(siblings, 1) if s is child)))
            else:
                components.append("*")
        child = parent
    components.reverse()

    xpath = ""
    for item in components:
        if "*" not in item:
            xpath = xpath + "/" + item
        else:
            xpath = xpath + "/" + item
            break

    return xpath


def download_file(url, directory):
	# Downloading of image
	try:
		r = requests.get(url, timeout=30)
		open(directory, "wb").write(r.content)
	except Exception:	
		return None


def write_file(path, contents):
	with open(path, "w+", encoding='utf-8') as f:
		f.write(contents)
	f.close()


# Function to recursively remove a particular path (folder)
def remove_folder(path):
	if len(os.listdir(path))==0:
		rmtree(path)


# Initialize list of known benign websites
def initialize_alexa(path):
	return list(filter(None, set(open(path,'r', encoding = "utf-8").read().lower().split('\n'))))


# Add more rules to check for redirect?
def check_redirect(url):
	try:
		resp = requests.get(url, timeout = 30)
		status_code = resp.history
		# Even if successful, check if theres a redirect by checking javascript injects
		if "200" in str(resp):
			if status_code == []:
				# The website coder shouldn't modify the window.location.href unless its an inject?
				if "window.location.href" in resp.text:
					find_url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', resp.text)
					if find_url:
						print("[*] WARNING: Redirection via JS inject from " + url + " to " + "".join(find_url))
						return "".join(find_url)
				else:
					print("[*] No Redirection")
					return url

			elif "200" in str(status_code):
				# No redirection
				print("[*] No Redirection")
				return url

		# Check for normal redirection with resp.history
		if ("301" in str(status_code) or "302" in str(status_code)):
			print("[*] Redirected from " + url + " to " + resp.url)
			return resp.url
	except Exception:
		print("[*] Failed to check redirect")
		print("[*] Website might be dead!")
		return None


# HTML Heuristics parsing
def html_heuristics(driver, timing_path):
	start_time = time.time()

	# Data structures and path initialization
	potential_image_set = set()
	coordinates_path = os.path.join(output_folder, "html_coords.txt")
	############################################################################################
	# HTML PARSING OCCURS HERE #
	############################################################################################
	start_time = time.time()
	############################################################################################
	# DATA IS ONLY SCRAPPED FROM HTML SOURCES #
	############################################################################################
	# Extracting tag "a"
	try:
		elems = driver.find_elements_by_tag_name("a")
		for elem in elems:		
			potential_image_set.add(elem)		
	except Exception:
		pass

	# Extracting tag "img"
	print("Extracting from HTML elements...")
	try:
		elems = driver.find_elements_by_tag_name("img")
		for elem in elems:
			potential_image_set.add(elem)
	except Exception:
		pass

	# Extracting tag "svg"
	try:
		elems = driver.find_elements_by_tag_name("svg")
		for elem in elems:
			potential_image_set.add(elem)
	except Exception:
		pass

	# Extracting tag "link"
	try:
		elems = driver.find_elements_by_tag_name("link")
		for elem in elems:
			if "image" in elem['type']:
				potential_image_set.add(elem)
	except Exception:
		pass

	# Extracting CSS embedded in HTML file (not separated)
	# Examples in HTML file: <body style = "background-image: url ....">"
	try:
		elems = driver.find_elements_by_xpath("//*")
		for elem in elems:
			if "none" not in elem.value_of_css_property("background-image"):
				potential_image_set.add(elem)
	except Exception:
		pass

	# First creating a dictionary to store data of css pages with links and class names
	dictionary_images = {}
	############################################################################################
	# DATA IS SCRAPPED FROM CSS SOURCE
	############################################################################################
	print("Extracting from CSS elements...")
	try:
		elems = driver.find_elements_by_tag_name("link")
		for elem in elems:
			try:
				link = elem.get_attribute('href')
				if ".css" in link:
					# Parsing the CSS data straight away to download images
					with open(css_save_path, "r") as f:
						data = f.read()

					rules = tinycss2.parse_stylesheet(
					    data
					)

					# IDENT TOKEN = "class name" --> Identification Token
					# URL TOKEN = if a CSS element contains a URL (likely due to images)
					# Parsing the rules to grab images (URL)
					# STILL HAVE LOTS OF ROOM FOR IMPROVEMENT FOR HEURISTICS HERE 

					for rule in rules:
						try:
							content = rule.content
							if content:
								for element in content:
									# Extract URL and check if it is an image
									# IF TRUE -> Extract the class names and store URL and classname to dictionary to map back to HTML 
									# IF TRUE -> means an image element is found in CSS page
									if element.type == "url" and test_link_extension(element.value):
										############################################################################################
										# PARSING TO EXTRACT ELEMENTS 
										############################################################################################
										class_object = rule.prelude
										temporary_classlist = []
										index = len(class_object)-1
										
										# Checking if it is a standalone one token
										if len(class_object) == 1:
											if class_object[index-1].type == "hash":
												temporary_classlist.append(("id", class_object[index-1]))
											elif class_object[index-1].value == ".":
												temporary_classlist.append(("class", class_object[index-1]))

										while (index >= 0):
											if (class_object[index].type == "ident" and (class_object[index-1].type=="literal")):
												# class separator
												if(class_object[index-1].value == "."):
													temporary_classlist.append(("class", class_object[index]))
													break
												elif(class_object[index-1].type == "hash"):
													temporary_classlist.append(("id", class_object[index-1]))
													break
												else:
													temporary_classlist.append(("tag", class_object[index]))
													break
											elif (class_object[index].type == "ident" and (class_object[index-1].type=="whitespace")):
												# class separator
												if(class_object[index-2].value == "."):
													temporary_classlist.append(("class", class_object[index]))
													break
												elif(class_object[index-2].type == "hash"):
													temporary_classlist.append(("id", class_object[index-2]))
													break
												else:
													temporary_classlist.append(("tag", class_object[index]))
													break
								
											index -=1

										dictionary_images[element] = temporary_classlist
									else:
										continue
						except AttributeError:
							continue

			except Exception:
				continue
	except Exception:
		# print("Element in not attached to page document")
		pass

	# TO-DO 
	# Improve the algorithm here
	# Current implementation just uses last path, should use entire tree traversed
	for img, path in dictionary_images.items():
		if img and path:
			type = path[0][0]
			token = path[0][1].value
			if type == "class":
				element = driver.find_elements_by_class_name(token)
			elif type =="id":
				element = driver.find_elements_by_id(token)
			else:
				element = driver.find_elements_by_tag_name(token)

			if element:
				for item in element:
					potential_image_set.add(item)
			else:
				continue

	############################################################################################
	# EXTRACTING COORDINATES FROM ALL SOURCES
	# Write to file
	############################################################################################			
	# All the combined image elements
	for item in potential_image_set:
		try:
			with open(coordinates_path, "a+") as f:
				# The location is the coordinates of the top left hand corner
				x1 = item.rect["x"]
				y1 = item.rect["y"]
				x2 = x1 + int(item.rect["width"])
				y2 = y1 + int(item.rect["height"])
				f.write(str((x1,y1,x2,y2)))
				f.write("\n")
		except TypeError:
			continue
		except Exception:
			# Catches all other exceptions
			continue

	total_time = time.time() - start_time
	with open(timing_path, "a+") as f:
		f.write("HTML Ruled Based: " + str(total_time))
		f.write("\n")


def extract_all_coordinates(driver, content, output_folder):
	############################################################################################
	# Full extraction of all coordinates
	############################################################################################
	# Using descendants method (traverse all)
	# Speed comparison to BFS is comparatively the same since need to traverse  through all nodes without giving up branches
	# DFS requires less memory 
	try:
		soup = BeautifulSoup(content, "lxml")
		body_portion = soup.find("body")
	except Exception:
		return 

	# Initializing file paths to store data
	all_coordinates_path = os.path.join(output_folder, "all_coordinates.txt")
	all_coordinates = set()

	if hasattr(body_portion, "descendants"):
	    for kiddo in body_portion.descendants:
	        try:
	            xpath = xpath_creator(kiddo)
	            element = driver.find_element_by_xpath(xpath)
	        except:
	            continue

	        # If theres element, try to get the current location
	        try:
	            if element:       
	                x1 = float(element.rect["x"])
	                y1 = float(element.rect["y"])
	                x2 = float(x1 + int(element.rect["width"]))
	                y2 = float(y1 + int(element.rect["height"]))
	                all_coordinates.add((x1, y1, x2, y2))
	        except Exception:
	            continue

	with open(all_coordinates_path, "w+") as f:
	    for item in all_coordinates:
	        f.write(str(item)+"\n")

# --start-maximized may not work so well because headless does not recognize resolution size
# therefore, windowsize has to be explicitly specified
def initialize_chrome_settings():
	options = webdriver.ChromeOptions()
	options.add_argument('--ignore-certificate-errors')
	options.add_argument('--ignore-certificate-errors-spki-list')
	options.add_argument('--ignore-ssl-errors')
	options.add_argument("--start-maximized")
	options.add_argument("--headless")
	options.add_argument("--incognito")
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument("--window-size=1920,1080")
	options.add_argument("--enable-javascript")
	options.add_argument("--disable-gpu")

	return options
			


############################################################################################
# MAIN CODE #
############################################################################################
def main(url, driver, output_folder):
	############################################################################################
	# Screenshot portion #
	############################################################################################
	# Please pre-fix these settings from "config.py" file to integrate these variables
	alexa = main_config.alexa
	alexa_list = initialize_alexa(alexa)

	# Check if domain re-directs
	# TO DO: Perhaps change to a status code instead
	url_to_check = check_redirect(url)
	
	if url_to_check is None:
		return (None, None, None)

	# Only testing the URLs that are not in alexa_list (assumed to be secure)
	if urlparse(url_to_check).netloc in alexa_list:
		print("In alexa list!")
		return (None, None, None)
	else:
		# Instantiating folder paths to save documents to
		if not os.path.exists(output_folder):
			os.makedirs(output_folder)

		screenshot_path = os.path.join(output_folder, "shot.png")
		info_path = os.path.join(output_folder, "info.txt")
		html_path = os.path.join(output_folder, "html.txt")
		timing_path = os.path.join(output_folder, "timings.txt")

		try:
			req = requests.get(url_to_check, verify=False, timeout = 30)
			req.raise_for_status()
		except Exception:
			print("Error!, removing folder: " + output_folder)
			remove_folder(output_folder)
			return (None, None, None)

		# Checking if website is still alive	
		try:
			status_code = requests.get(url, timeout = 30).status_code
		except Exception:
			print("Error! Removing folder: " + output_folder)
			remove_folder(output_folder)
			return (None, None, None)

		if status_code != 200:
			return (None, None, None)

		# Page is alive, checking for presence of frame and iframe
		else:
			iframe = ""
			frame = ""
			try:
				driver.get(url_to_check)
				frame = driver.find_elements_by_xpath("//frame")
				iframe = driver.find_elements_by_xpath("//iframe")
			except Exception:
				remove_folder(output_folder)
				return (None, None, None)

			# Current method is mutually exclusive 
			# Further investigate how to collectively get all HTML (?)
			new_frame = ""
			if frame and not iframe:
				for element in frame:
					try:
						new_frame = element.get_attribute("src")
						break
					except Exception:
						continue
			elif iframe and not frame:
				for element in iframe:
					try:
						new_frame = element.get_attribute("src")
						break
					except Exception:
						continue

			# Accounting for websites that are invalid to reduce noise
			try:
				if new_frame:
					driver.get(new_frame)
					content = driver.page_source
				else:
					content = driver.page_source
			except Exception:
				return (None, None, None)

			
			# Screenshot, HTML code and URL
			driver.save_screenshot(screenshot_path)
			write_file(html_path, content)
			write_file(info_path, url_to_check)

			# Check if webpage is purely empty 
			# Have a function here to check if webpage is really empty 
			# Assumes that the entire page should have 1 div tag
			if "<div" not in content and req.text == "":
				print("No point saving HTML as HTML is likely to be empty")
				return (None, None, None)
		
	extract_all_coordinates(driver, content, output_folder)
	# html_heuristics(driver, timing_path)

	return url, url_to_check, output_folder


# # Only uncomment this for individual script testing!
# if __name__ == "__main__":
# 	# Initializing chrome driver settings to run headless, windows resolution etc.
# 	chrome_driver_options = initialize_chrome_settings()
# 	chromedriver = main_config.chromedriver
# 	try:
# 		print("Starting driver!")
# 		driver = webdriver.Chrome(chromedriver, options=chrome_driver_options)
# 		driver.set_page_load_timeout(30)
# 		driver.set_script_timeout(30)
# 		print("Session is created!")
# 	except SessionNotCreatedException as snce:
# 		print("Session not Created!")

# 	url = "http://www.comercialmattos.com.br/login.html"

# 	main(url, driver, "test")