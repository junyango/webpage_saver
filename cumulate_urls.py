################################################################################################################
## This code is meant to take in openphish data and eventually produce a cumulative_urls.txt ##
## Cumulative_urls.txt includes url and brand name, separated by a delimiter of a tab "\t" ##
## Usage: Input folder containing openphish text files, example in this case, python cumulate_urls.py -f 1mayto13june" 
################################################################################################################

import os
import argparse
import json


def readData(dataUrl):
    fopen=open(dataUrl, 'r')
    x=fopen.read()
    rawdata=x.split('}')
    listdict=[]
    for i in rawdata:
        try:
            i=i.lstrip(', ')
            i=i.lstrip('[')
            i=i.replace('}]','')
            i=i+'}'
            listdict.append(json.loads(i))
        except Exception:
             continue
    fopen.close()
    return listdict


# Ensure no duplicates
cumulative_urls = set()
parser = argparse.ArgumentParser()
parser.add_argument('-f', "--folder", help='Input folder for collected openphish urls', required=True)
args = parser.parse_args()

for file in os.listdir(args.folder):
	full_path_file = os.path.join(args.folder, file)
	url_target = readData(full_path_file)
	for item in url_target:
		cumulative_urls.add((item['url'], item['brand']))
	
	print("Done with: " + str(file))

file_to_write = "cumulative_urls.txt"

print(len(cumulative_urls))
with open(file_to_write, "w+") as f:
	for item in cumulative_urls:
		url, brand = item
		f.write(url+"\t")
		f.write(brand+"\n")