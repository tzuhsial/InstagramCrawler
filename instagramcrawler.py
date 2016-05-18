"""
    TODO: Check target validity( Private | invalid usernames | weird hashtags )

"""

import argparse
import codecs
import logging
import json
import os
import pdb
import re
import time
import traceback
from urlparse import urljoin

from requests_futures.sessions import FuturesSession
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

"""
    Selenium related
"""
# Scroll downs script
SCROLL_UP   = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"
# Elements
CSS_LOGIN = "a[class='/accounts/login/']"
CSS_LOAD_MORE = "a._oidfu"
CSS_RIGHT_ARROW = "a[class='_de018 coreSpriteRightPaginationArrow']"
# XPATH
TIME_TO_CAPTION_PATH = "../../following-sibling::ul/*/*/span"

"""
    Define Expected Condition
"""
class url_change(object):
    def __init__(self, prev_url):
        self.prev_url = prev_url
    def __call__(self, driver):
        return self.prev_url != driver.current_url

class log_in(object):
    def __init__(self):
        pass
    def __call__(self, driver):
        return 'logged-in' in driver.page_source
"""
    Instagram Crawler
"""
class InstagramCrawler(object):
    def __init__(self,dir_prefix = './data/'):

        self.driver = webdriver.Firefox()
        #self.driver = webdriver.Chrome(executable_path='./chromedriver')
        self.dir_prefix = ( dir_prefix + '/' if not dir_prefix.endswith('/') else dir_prefix )
        self.host = "http://www.instagram.com"

        # Download and Saving
        self.session = FuturesSession(max_workers=10)

        # Photo links and captions
        self.photo_links = None
        self.captions = None
        self.userlist = None

    def __del__(self):
        if self.driver:
            self.driver.close()

    def login(self):
        self.get(urljoin(self.host,"accounts/login/"))
        WebDriverWait(driver, 60).until(log_in())
        return self

    def browse(self, target, crawl_type):
        """
            Scroll to the correct number of posts
        """

        self.photo_links = None
        self.captions = None
        self.userlist = None

        self.target = target # username | hastag

        self.crawl_type = crawl_type
        if crawl_type in ["username","followers"]:
            url = urljoin(self.host,target)
        elif crawl_type == "hashtag":
            url = urljoin(self.host, 'explore/tags/' + target)
        else:
            raise Exception("Invalid crawl_type '{0}'")

        self.driver.get(url)

        return self

    def crawl(self,number=None,caption=False):

        self.number = self._set_post_num(number)

        self.driver.execute_script(SCROLL_DOWN)

        if self.number > 12:
            loadmore = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, CSS_LOAD_MORE))
            )
            loadmore.click()

            num_to_scroll = (self.number - 12)/12 + 1
            for _ in range(num_to_scroll):
                self.driver.execute_script(SCROLL_DOWN)
                time.sleep(0.05)
                self.driver.execute_script(SCROLL_UP)
                time.sleep(0.05)

        self.photo_links = self._crawl_photo_links()

        assert len(self.photo_links) == self.number, \
            "Numbers of data and target number do not match!"

        if caption:
            self.captions = self._crawl_captions()
            assert len(self.photo_links) == len(self.captions),\
                "Number of photos and captions do not match!"

        return self

    def save(self):
        target_dir = self.dir_prefix + self.target + '/'
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        def bg_cb(ses,resp,idx):
            with open(target_dir+str(idx)+".jpg",'w') as f:
                f.write(resp.content)

        def bg_cb_factory(idx):
            return lambda sess, resp: bg_cb(sess, resp, idx)

        # Send async requests and cache in list
        # Don't know why but saving images in callback is slower, though
        start_time = time.time()
        image_responses = [ self.session.get(self.photo_links[idx])#, \
                            #background_callback = bg_cb_factory(idx)) \
                            for idx in range(self.number) ]

        for idx in range(self.number):
            img = str(idx) + '.jpg'
            resp = image_responses[idx].result()

            with open(target_dir + img,'w') as f:
                f.write(resp.content)

            if self.captions:
                cap = str(idx) + '.txt'
                with codecs.open(target_dir + cap,'w','utf-8') as f:
                    f.write(self.captions[idx])

        time_taken = time.time() - start_time
        logging.info("Download took {} seconds...".format(time_taken))

        return self

    def _set_post_num(self, number_to_download):

        post_num_info = re.search(r'\"media":{"count":\d+', self.driver.page_source).group()
        post_num = re.findall(r'\d+', post_num_info)[0]

        post_num = ( 0 if not post_num else int(post_num) )

        # number_to_download should be a string instance
        if number_to_download == "all":
            return post_num
        elif number_to_download.isdigit():
            if int(number_to_download) > post_num:
                return post_num
            else:
                return int(number_to_download)
        else:
            raise Exception("Number should be 'all' or an integer")

    def _crawl_photo_links(self):
        encased_photo_links = re.finditer(r'src="([https]+:...[\/\w \.-]*..[\/\w \.-]*'
                            r'..[\/\w \.-]*..[\/\w \.-].jpg)', self.driver.page_source)
        photo_links = [ m.group(1) for m in encased_photo_links ]

        if self.crawl_type == 'hashtag':
            begin = 0
            end = self.number
        else: # Exclude profile pic
            begin = 1
            end = self.number + 1

        return photo_links[begin:end]

    def _crawl_captions(self):
        # Initialize Return List
        captions = []
        for post_num in range(self.number):
            if post_num == 0: # Click on the first post
                # For Chrome
                #self.driver.find_element_by_class_name('_ovg3g').click()
                # Firefox
                self.driver.find_element_by_xpath("//a[contains(@class, '_8mlbc _vbtk2 _t5r8b')]").click()
                if self.number != 1: # If user has only one post
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,CSS_RIGHT_ARROW))
                    )

            elif self.number != 1: # Click and parse
                url_before = self.driver.current_url
                self.driver.find_element_by_css_selector(CSS_RIGHT_ARROW).click()
                # Wait until the page has loaded
                WebDriverWait(self.driver, 10).until(
                    url_change(url_before)
                )
            captions.append(self._parse_caption())

        return captions

    def _parse_caption(self):
        time = WebDriverWait(self.driver,10).until(
            EC.presence_of_element_located((By.TAG_NAME, "time"))
        )
        try:
            caption = time.find_element_by_xpath(TIME_TO_CAPTION_PATH).text
        except NoSuchElementException: # Forbidden
            caption = ""

        return caption
    """
    def _crawl_followers(self):
        try:
            driver.find_element_by_css_selector(CSS_LOGIN).click()
            self.get(urljoin(self.host,self.target))
        except: NoSuchElementException:
            logging.info("You have already loggined in")
    """
def main():
    parser = argparse.ArgumentParser(description='Instagram Crawler')

    parser.add_argument('-f','--file',type=str, help='List of username | hashtag')
    parser.add_argument('-t','--type',type=str, help = 'username | hashtag | followers')
    parser.add_argument('-c','--caption', action='store_true', help='Add this flag to download caption')
    parser.add_argument('-n', '--number', default='12', help='Number of posts to download: integer or "all"')
    parser.add_argument('-d', '--dir', type=str, default = './data/',
                            help='directory to save results')
    args = parser.parse_args()

    crawler = InstagramCrawler(args.dir)

    with open(args.file,'r') as fin:
        for line in fin.readlines():
            target = line.strip()
            try:
                crawler.browse(target,args.type).crawl(args.number,args.caption).save()
            except:
                logging.info("Crawl {0} {1} failed".format(args.type,target))

if __name__ == "__main__":
    main()
