"""
    TODO: Check validity( Private | invalid usernames | weird hashtags )
"""
import argparse
import codecs
import logging
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
CSS_LOGIN = "a[href='/accounts/login/']"
CSS_EXPLORE = "a[href='/explore/']"
CSS_LOAD_MORE = "a._oidfu"
CSS_RIGHT_ARROW = "a[class='_de018 coreSpriteRightPaginationArrow']"
CSS_FOLLOWERS = "a[href='/{}/followers/']"
# XPATH
FOLLOWER_PATH = "//*[contains(text(), 'Followers')]"
TIME_TO_CAPTION_PATH = "../../following-sibling::ul/*/*/span"

"""
    Define Expected Condition
"""
class url_change(object):
    def __init__(self, prev_url):
        self.prev_url = prev_url
    def __call__(self, driver):
        return self.prev_url != driver.current_url
"""
    Instagram Crawler
"""
class InstagramCrawler(object):
    def __init__(self,dir_prefix = './data/'):

        self.driver = webdriver.Firefox()
        self.dir_prefix = ( dir_prefix + '/' if not dir_prefix.endswith('/') else dir_prefix )
        self.host = "http://www.instagram.com"

        # Download and Saving
        self.session = FuturesSession(max_workers=10)

    def __del__(self):
        if self.driver:
            self.driver.close()

    def login(self):
        self.driver.get(urljoin(self.host,"accounts/login/"))
        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CSS_EXPLORE))
        )

    def clear(self):
        self.photo_links = None
        self.captions = None
        self.userlist = None

    def browse(self, target, crawl_type):
        """
            Scroll to the correct number of posts
        """
        self.clear()

        self.target = target
        if not crawl_type in ['photos','followers']:
            raise Exception("Invalid crawl_type: {0}".format(crawl_type))
        self.crawl_type = crawl_type

        if target.startswith("#"): # Hashtag
            self.url = urljoin(self.host, 'explore/tags/' + target.lstrip('#'))
            if self.crawl_type == "followers":
                raise Exception("Hashtags don't have followers!")
        else:
            self.url = urljoin(self.host,target)

        self.driver.get(self.url)

        return self

    def crawl(self,number=None,caption=False):
        self.number = self._set_post_num(number)

        if self.crawl_type == "photos":
            self.photo_links = self._crawl_photo_links()

            assert len(self.photo_links) == self.number, \
                "Numbers of data and target number do not match!"

            if caption:
                self.captions = self._crawl_captions()
                assert len(self.photo_links) == len(self.captions),\
                    "Number of photos and captions do not match!"

        elif self.crawl_type == "followers":
            self.followerlist = self._crawl_followers()
            assert len(self.followerlist) == self.number,\
                "Number of followers and number do not match!"

        return self

    def save(self):
        target_dir = self.dir_prefix + self.target.lstrip('#') + '/'
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        if self.crawl_type == "photos":
            # Send async requests and cache in list
            image_responses = [ self.session.get(self.photo_links[idx]) \
                                for idx in range(self.number) ]

            for idx in range(self.number):
                resp = image_responses[idx].result()

                img = str(idx) + '.jpg'
                with open(target_dir + img,'w') as f:
                    f.write(resp.content)

                if self.captions:
                    cap = str(idx) + '.txt'
                    with codecs.open(target_dir + cap,'w','utf-8') as f:
                        f.write(self.captions[idx])

        elif self.crawl_type == "followers":
            with open(target_dir + "followers{}.txt".format(self.number),'w') as f:
                for follower in self.followerlist:
                    f.write(follower + '\n')

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

        encased_photo_links = re.finditer(r'src="([https]+:...[\/\w \.-]*..[\/\w \.-]*'
                            r'..[\/\w \.-]*..[\/\w \.-].jpg)', self.driver.page_source)
        photo_links = [ m.group(1) for m in encased_photo_links ]

        if self.target.startswith('#'):
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
    def _crawl_followers(self):
        try:
            self.driver.find_element_by_css_selector(CSS_LOGIN)
            self.login()
            self.driver.get(self.url)
        except:
            logging.info("Already logged in!")

        followers = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,CSS_FOLLOWERS.format(self.target)))
        )
        followers.click()
        time.sleep(1)
        Followers = self.driver.find_element_by_xpath(FOLLOWER_PATH)
        List = Followers.find_element_by_xpath('..').find_element_by_tag_name('ul')

        List.click()
        cur_follower_num = len(List.find_elements_by_xpath('*'))

        if self.number > cur_follower_num:
            element = List.find_elements_by_xpath('*')[-1]

            while len(List.find_elements_by_xpath('*')) < self.number:
                element.send_keys(Keys.PAGE_DOWN)

            cur_follower_num = len(List.find_elements_by_xpath('*'))
            for _ in range(2*(self.number - cur_follower_num)/10):
                element.send_keys(Keys.PAGE_DOWN)

        followers =  []
        for ele in List.find_elements_by_xpath('*')[:self.number]:
            followers.append(ele.text.split('\n')[0])

        return followers

def main():
    parser = argparse.ArgumentParser(description='Instagram Crawler')
    parser.add_argument('-q','--query',type=str, help="target to crawl, add '#' for hashtags")
    parser.add_argument('-t','--type',type=str, help = 'photos | followers')
    parser.add_argument('-n', '--number', default='12', help='Number of posts to download: integer or "all"')
    parser.add_argument('-c','--caption', action='store_true', help='Add this flag to download caption when downloading photos')
    parser.add_argument('-d', '--dir', type=str, default = './data/',
                            help='directory to save results')
    args = parser.parse_args()

    crawler = InstagramCrawler(args.dir)

    try:
        crawler.browse(args.query,args.type).crawl(args.number,args.caption).save()
    except:
        err_msg = traceback.format_exc()
        print err_msg
        logging.info("Crawl {0} {1} failed".format(args.type,args.query))

if __name__ == "__main__":
    main()
