*******************************************************************
Selenium ChromeDriver
*******************************************************************
1. Please ensure that you have chromedriver.exe installed, otherwise, head to https://chromedriver.chromium.org/downloads
2. Please select the relevant Google Chrome versions and download and unzip the exe into the folder

*******************************************************************
main_config.py
*******************************************************************
1. In this file, you can toggle the settings of your folders of chromedriver, alexa_domains here

*******************************************************************
To install the requirements for this project
*******************************************************************
1. Create a virtualenv by using virtualenv venv in this folder, and activate virtualenv
2. pip install -r requirements.txt

*******************************************************************
PywebCopy settings
*******************************************************************
1. Navigate to the venv folder, to look for site-package (pywebcopy)
2. Navigate to webpage.py and look for code snippet function (save_assets(self))
3: Edit the code in this manner:
      for elem in elms:
            elem.run()
            # with POOL_LIMIT:
            # t = threading.Thread(name=repr(elem), target=elem.run)
            # t.start()
            # self._threads.append(t)

The reason is the multi-threaded implementation of the download may cause the program to hang at times.
Even when the threads are manually joined, it could impose hanging problems as well.
This has been brought up to the developer and he suggested that single-threaded implementations will work without problems

*******************************************************************
To first generate URLS from OpenPhish data source:
*******************************************************************
1. Add all the txt files from OpenPhish database into a folder 
2. run cumulate_urls with arguments -f folder || Example: python cumulate_urls.py -f <folder from bullet point 1>
3. Output: cumulative_urls.txt in a set