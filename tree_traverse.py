from bs4 import BeautifulSoup
import bs4
import queue
from selenium import webdriver
import requests
from selenium.common.exceptions import *
import main_config
import re

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from PIL import Image
import time


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
    # options.add_argument("--enable-javascript")
    options.add_argument("--disable-gpu")

    return options


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


# Function finds intersection over union (overlapping between two bounding boxes)
def bbox_iou(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
      xA = max(boxA[0], boxB[0])
      yA = max(boxA[1], boxB[1])
      xB = min(boxA[2], boxB[2])
      yB = min(boxA[3], boxB[3])

      # compute the area of intersection rectangle
      interArea = abs(max((xB - xA, 0)) * max((yB - yA), 0))
      if interArea == 0:
          return 0
      # compute the area of both the prediction and ground-truth
      # rectangles
      boxAArea = abs((boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
      boxBArea = abs((boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

      # compute the intersection over union by taking the intersection
      # area and dividing it by the sum of prediction + ground-truth
      # areas - the interesection area
      iou = interArea / float(boxAArea + boxBArea - interArea)

      # return the intersection over union value
      return iou


chromedriver = main_config.chromedriver
options = initialize_chrome_settings()

try:
    print("Starting driver!")
    driver = webdriver.Chrome(chromedriver, options=options)
    driver.set_page_load_timeout(120)
    driver.set_script_timeout(60 )
    print("Session is created!")
except SessionNotCreatedException as snce:
    print("Session not Created!")


overlapping_elements = []
tree_coordinates = {}

# base_html = "D:/junyang/concurrent_crawler/bagarenochkocken.se/html.txt"
# render_html = "D:/junyang/concurrent_crawler/bagarenochkocken.se/bagarenochkocken.se/bagarenochkocken.se/index.html"
# yolo_coords = "D:/junyang/concurrent_crawler/bagarenochkocken.se/yolo_coords.txt"
# shot_path = "D:/junyang/concurrent_crawler/bagarenochkocken.se/shot.png"

# base_html = "D:/junyang/concurrent_crawler/Benign_1k/1.fm/html.txt"
# render_html = "D:/junyang/concurrent_crawler/Benign_1k/1.fm/www.1.fm/www.1.fm//08cf7715__hello.html"
# yolo_coords = "D:/junyang/concurrent_crawler/Benign_1k/1.fm/yolo_coords.txt"
# shot_path = "D:/junyang/concurrent_crawler/Benign_1k/1.fm/shot.png"

base_html = "D:/junyang/concurrent_crawler/Benign_1k/01webdirectory.com/html.txt"
render_html = "D:/junyang/concurrent_crawler/Benign_1k/01webdirectory.com/www.01webdirectory.com/www.01webdirectory.com/index.html"
yolo_coords = "D:/junyang/concurrent_crawler/Benign_1k/01webdirectory.com/yolo_coords.txt"
shot_path = "D:/junyang/concurrent_crawler/Benign_1k/01webdirectory.com/shot.png"

driver.get(render_html)


with open(base_html, encoding="utf-8") as fp:
    try:
        soup = BeautifulSoup(fp, "lxml")
    except Exception as e:
        print(e)
        pass

####################################################################
# ALGORITHM # 
####################################################################
start_time = time.time()

####################################################################
# BFS #
####################################################################
queue = []
visited = []

# Adding first layer of children into the queue first
body_portion = soup.find("body")
for item in body_portion.children:
    queue.append(item)

# html_coordinates file
html_file = "all_coordinates.txt"
all_coordinates = set()

while queue:
    element = queue.pop(0)   
    xpath = xpath_creator(element)
    try:
        selenium_element = driver.find_element_by_xpath(xpath)
    except:
        continue
    # Checking if xpath can be found
    if selenium_element:
        x1 = float(selenium_element.rect["x"])
        y1 = float(selenium_element.rect["y"])
        x2 = float(x1 + float(selenium_element.rect["width"]))
        y2 = float(y1 + float(selenium_element.rect["height"]))
        all_coordinates.add((x1, y1, x2, y2))
        plt.gca().add_patch(Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='y', facecolor='none'))
        if hasattr(element, 'children'):  # check for leaf elements
            for child in element.children:
                if child not in visited:
                    visited.append(child)
                    queue.append(child)


with open(html_file, "w+") as f:
    for item in all_coordinates:
        f.write(str(item)+"\n")

stop_time = time.time() - start_time

print("TIME TAKEN FOR THIS SHIT: " + str(stop_time))

plt.show()
driver.quit()

# # ####################################################################
# # # ALL SHIT
# # ####################################################################

# # html_coordinates file
# html_file = "all_coordinates_2.txt"
# all_coordinates = set()


# # Adding first layer of children into the queue first
# body_portion = soup.find("body")

# count = 0
# tree_path = []
# # Recursively find for children!
# if hasattr(body_portion, "descendants"):
#     for kiddo in body_portion.descendants:
#         count +=1
#         try:
#             xpath = xpath_creator(kiddo)
#             element = driver.find_element_by_xpath(xpath)
#         except:
#             continue

#         # If theres element, try to get the current location
#         try:
#             if element:       
#                 x1 = float(element.rect["x"])
#                 y1 = float(element.rect["y"])
#                 x2 = float(x1 + int(element.rect["width"]))
#                 y2 = float(y1 + int(element.rect["height"]))
#                 all_coordinates.add((x1, y1, x2, y2))
#         except Exception:
#             continue

# with open(html_file, "w+") as f:
#     for item in all_coordinates:
#         f.write(str(item)+"\n")

# stop_time = time.time() - start_time
# print("TIME TAKEN FOR THIS SHIT: " + str(stop_time))
# print(count)

# ##################################################################################################################
# # FINDING ELEMENT PATH #
# ##################################################################################################################
# overlapping_elements = []
# for last_child in tree_path:
#     xpath = xpath_creator(last_child)
#     try:
#         element = driver.find_element_by_xpath(xpath)
#     except:
#         continue

#     # If theres element, try to get the current location
#     try:
#         if element:       
#             x1 = float(element.rect["x"])
#             y1 = float(element.rect["y"])
#             x2 = float(x1 + int(element.rect["width"]))
#             y2 = float(y1 + int(element.rect["height"]))

#             element_bbox = [x1,y1,x2,y2]
#             for failed_coords in coord_yolo:
#                 result = bbox_iou(element_bbox, failed_coords)
#                 if result > 0:
#                     if xpath not in overlapping_elements:
#                         overlapping_elements.append(xpath)
#                         plt.gca().add_patch(Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='y', facecolor='none'))
#     except Exception:
#         continue

# stop_time = time.time() - start_time

# print("TIME TAKEN FOR THIS SHIT: " + str(stop_time))

# plt.show()
# driver.quit()




