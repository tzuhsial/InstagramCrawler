from __future__ import division

import argparse
import codecs
from collections import defaultdict
import os
import re
import sys
import time
try:
    from urlparse import urljoin
    from urllib import urlretrieve
except ImportError:
    from urllib.parse import urljoin
    from urllib.request import urlretrieve

import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# HOST
HOST = 'http://www.instagram.com'

# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = "a._8imhp._glz1g"
CSS_RIGHT_ARROW = "a[class='_de018 coreSpriteRightPaginationArrow']"
FIREFOX_FIRST_POST_PATH = "//a[contains(@class, '_8mlbc _vbtk2 _t5r8b')]"
TIME_TO_CAPTION_PATH = "../../following-sibling::ul/*/*/span"

# FOLLOWERS/FOLLOWING RELATED
CSS_EXPLORE = "a[href='/explore/']"
CSS_LOGIN = "a[href='/accounts/login/']"
CSS_FOLLOWERS = "a[href='/{}/followers/']"
CSS_FOLLOWING = "a[href='/{}/following/']"
FOLLOWER_PATH = "//div[contains(text(), 'Followers')]"
FOLLOWING_PATH = "//div[contains(text(), 'Following')]"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"

# For Caption Scraping
class url_change(object):
    def __init__(self, prev_url):
        self.prev_url = prev_url

    def __call__(self, driver):
        return self.prev_url != driver.current_url

# Crawler Class
class InstagramCrawler(object):
    def __init__(self):
        self._driver = webdriver.Firefox()

        self.data = defaultdict(list)

    def login(self):
        self._driver.get(urljoin(HOST, "accounts/login/"))
        print("")
        WebDriverWait(self._driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CSS_EXPLORE))
        )

    def quit(self):
        self._driver.quit()

    def crawl(self, dir_prefix, query, crawl_type, number, caption):
        print("dir_prefix: {}, query: {}, crawl_type: {}, number: {}, caption: {}"
              .format(dir_prefix, query, crawl_type, number, caption))

        if crawl_type == "photos":
            # Browse target page
            self.browse_target_page(query)
            # Scroll down until target number photos is reached
            self.scroll_to_num_of_posts(number)
            # Scrape photo links
            self.scrape_photo_links(number, is_hashtag=query.startswith("#"))
            # Scrape captions if specified
            if caption is True:
                self.click_and_scrape_captions(number)

        elif crawl_type in ["followers", "following"]:
            # Need to login first before crawling followers/following
            print("You will need to login to crawl {}".format(crawl_type))
            self.login()
            # Then browse target page
            assert not query.startswith(
                '#'), "Hashtag does not have followers/following!"
            self.browse_target_page(query)
            # Scrape captions
            self.scrape_followers_or_following(crawl_type, query, number)

        # Save to directory
        print("Saving...")
        self.download_and_save(dir_prefix, query, crawl_type)

        # Quit driver
        print("Quitting driver...")
        self.quit()

    def browse_target_page(self, query):
        # Browse Hashtags
        if query.startswith('#'):
            relative_url = urljoin('explore/tags/', query.strip('#'))
        else:  # Browse user page
            relative_url = query

        target_url = urljoin(HOST, relative_url)

        self._driver.get(target_url)

    def scroll_to_num_of_posts(self, number):
        # Get total number of posts of page
        num_info = re.search(r'\], "count": \d+',
                             self._driver.page_source).group()
        num_of_posts = int(re.findall(r'\d+', num_info)[0])
        print("posts: {}, number: {}".format(num_of_posts, number))
        number = number if number < num_of_posts else num_of_posts

        # scroll page until reached
        loadmore = WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, CSS_LOAD_MORE))
        )
        loadmore.click()

        num_to_scroll = int((number - 12) / 12) + 1
        for _ in range(num_to_scroll):
            self._driver.execute_script(SCROLL_DOWN)
            time.sleep(0.1)
            self._driver.execute_script(SCROLL_UP)
            time.sleep(0.1)

    def scrape_photo_links(self, number, is_hashtag=False):
        print("Scraping photo links...")
        encased_photo_links = re.finditer(r'src="([https]+:...[\/\w \.-]*..[\/\w \.-]*'
                                          r'..[\/\w \.-]*..[\/\w \.-].jpg)', self._driver.page_source)

        photo_links = [m.group(1) for m in encased_photo_links]

        print("Number of photo_links: {}".format(len(photo_links)))

        begin = 0 if is_hashtag else 1

        self.data['photo_links'] = photo_links[begin:number + begin]

    def click_and_scrape_captions(self, number):
        print("Scraping captions...")
        captions = []

        for post_num in range(number):
            if post_num == 0:  # Click on the first post
                # Chrome
                # self._driver.find_element_by_class_name('_ovg3g').click()
                self._driver.find_element_by_xpath(
                    FIREFOX_FIRST_POST_PATH).click()

                if number != 1:  #
                    WebDriverWait(self._driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, CSS_RIGHT_ARROW)
                        )
                    )

            elif number != 1:  # Click Right Arrow to move to next post
                url_before = self._driver.current_url

                self._driver.find_element_by_css_selector(
                    CSS_RIGHT_ARROW).click()

                # Wait until the page has loaded
                try:
                    WebDriverWait(self._driver, 5).until(
                        url_change(url_before))
                except TimeoutException:
                    print("Time out in caption scraping at number {}".format(post_num))
                    break

            # Parse caption
            try:
                time_element = WebDriverWait(self._driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "time"))
                )
                caption = time_element.find_element_by_xpath(
                    TIME_TO_CAPTION_PATH).text
            except NoSuchElementException:  # Forbidden
                caption = ""

            captions.append(caption)

        self.data['captions'] = captions

    def scrape_followers_or_following(self, crawl_type, query, number):
        print("Scraping {}...".format(crawl_type))
        if crawl_type == "followers":
            FOLLOW_ELE = CSS_FOLLOWERS
            FOLLOW_PATH = FOLLOWER_PATH
        elif crawl_type == "following":
            FOLLOW_ELE = CSS_FOLLOWING
            FOLLOW_PATH = FOLLOWING_PATH

        # Locate Crawl Type
        follow_ele = WebDriverWait(self._driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, FOLLOW_ELE.format(query)))
        )
        follow_ele.click()
        time.sleep(1)
        title = self._driver.find_element_by_xpath(FOLLOW_PATH)
        List = title.find_element_by_xpath('..').find_element_by_tag_name('ul')
        List.click()

        # Loop through list till target number is reached
        num_of_shown_follow = len(List.find_elements_by_xpath('*'))

        while len(List.find_elements_by_xpath('*')) < number:
            element = List.find_elements_by_xpath('*')[-1]
            # Work around for now => should use selenium's Expected Conditions!
            try:
                element.send_keys(Keys.PAGE_DOWN)
            except Exception as e:
                time.sleep(0.1)

        follow_items = []
        for ele in List.find_elements_by_xpath('*')[:number]:
            follow_items.append(ele.text.split('\n')[0])

        self.data[crawl_type] = follow_items

    def download_and_save(self, dir_prefix, query, crawl_type):
        # Check if is hashtag
        dir_name = query.lstrip(
            '#') + '.hashtag' if query.startswith('#') else query

        dir_path = os.path.join(dir_prefix, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        print("Saving to directory...{}".format(dir_path))

        # Save Photos
        for idx, photo_link in enumerate(self.data['photo_links'], 0):
            sys.stdout.write("\033[F")
            print("Downloading {} image...".format(idx + 1))
            # Filename
            _, ext = os.path.splitext(photo_link)
            filename = str(idx) + ext
            filepath = os.path.join(dir_path, filename)
            # Send image request
            urlretrieve(photo_link, filepath)

        # Save Captions
        for idx, caption in enumerate(self.data['captions'], 0):

            filename = str(idx) + '.txt'
            filepath = os.path.join(dir_path, filename)

            with codecs.open(filepath, 'w', encoding='utf-8') as fout:
                fout.write(caption + '\n')

        # Save followers/following
        filename = crawl_type + '.txt'
        filepath = os.path.join(dir_path, filename)
        if len(self.data[crawl_type]):
            with codecs.open(filepath, 'w', encoding='utf-8') as fout:
                for fol in self.data[crawl_type]:
                    fout.write(fol + '\n')


def main():
    #   Arguments  #
    parser = argparse.ArgumentParser(description='Instagram Crawler')
    parser.add_argument('-d', '--dir_prefix', type=str,
                        default='./data/', help='directory to save results')
    parser.add_argument('-q', '--query', type=str, default='instagram',
                        help="target to crawl, add '#' for hashtags")
    parser.add_argument('-t', '--crawl_type', type=str,
                        default='photos', help="Options: 'photos' | 'followers' | 'following'")
    parser.add_argument('-n', '--number', type=int, default=12,
                        help='Number of posts to download: integer or "all"')
    parser.add_argument('-c', '--caption', action='store_true',
                        help='Add this flag to download caption when downloading photos')
    args = parser.parse_args()
    #  End Argparse #

    crawler = InstagramCrawler()
    crawler.crawl(dir_prefix=args.dir_prefix, query=args.query, crawl_type=args.crawl_type, number=args.number,
                  caption=args.caption)


if __name__ == "__main__":
    main()
