import argparse
import os
import re
import sys
import time
from urlparse import urljoin

import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# HOST
HOST = 'http://www.instagram.com'

# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = "a._8imhp._glz1g"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"

class InstagramCrawler(object):
    def __init__(self):
        self._driver = webdriver.Firefox()

        self.data = {}

    def __del__(self):
        self._driver.quit()

    def crawl(self, query, crawl_type, number, caption, dir_prefix):
        print("Query: {}, type: {}, number: {}, caption: {}".format(query,crawl_type, number, caption))

        # Browse url
        self.browse_target_page(query, crawl_type)

        # Scroll down until target Number photos is reached
        self.scroll_until_target_number(number)

        # Start crawling
        self.scrape_photo_links(number)

        # Save to directory
        self.download_and_save(dir_prefix,query)
        import pdb; pdb.set_trace()

    def browse_target_page(self, query, crawl_type):
        target_url = urljoin(HOST,query)
        self._driver.get(target_url)

    def scroll_until_target_number(self, number):
        # Get total number of posts of page
        num_info = re.search(r'\], "count": \d+', self._driver.page_source).group()
        num_of_posts = int(re.findall(r'\d+', num_info)[0])
        print("posts: {}, number: {}".format(num_of_posts,number))
        number = number if number < num_of_posts else num_of_posts

        # scroll page until reached
        loadmore = WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, CSS_LOAD_MORE))
        )
        loadmore.click()

        num_to_scroll = (number - 12) / 12 + 1
        for _ in range(num_to_scroll):
            self._driver.execute_script(SCROLL_DOWN)
            time.sleep(0.1)
            self._driver.execute_script(SCROLL_UP)
            time.sleep(0.1)

    def scrape_photo_links(self, number):

        encased_photo_links = re.finditer(r'src="([https]+:...[\/\w \.-]*..[\/\w \.-]*'
                                          r'..[\/\w \.-]*..[\/\w \.-].jpg)', self._driver.page_source)

        photo_links = [m.group(1) for m in encased_photo_links]

        print("Number of photo_links: {}".format(len(photo_links)))

        self.data['photo_links'] = photo_links[:number]

    def download_and_save(self, dir_prefix, query):

        dir_path = os.path.join(dir_prefix,query)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        for idx, photo_link in enumerate(self.data['photo_links'],0):
            print("Downloading {} image...".format(idx+1))
            #sys.stdout.write("\033[F")

            # Send image request
            res = requests.get(photo_link)

            # Filename
            _, ext = os.path.splitext(photo_link)
            filename = str(idx) + ext

            with open(os.path.join(dir_path,filename),'w') as fout:
                fout.write(res.content)

def main():
    # Arguments #
    parser = argparse.ArgumentParser(description='Instagram Crawler')
    parser.add_argument('-q', '--query', type=str, default='instagram', help="target to crawl, add '#' for hashtags")
    parser.add_argument('-t', '--crawl_type', type=str, default='photos', help='photos | followers | following')
    parser.add_argument('-n', '--number', type=int, default=12, help='Number of posts to download: integer or "all"')
    parser.add_argument('-c', '--caption', action='store_true', help='Add this flag to download caption when downloading photos')
    parser.add_argument('-d', '--dir_prefix', type=str, default='./data/', help='directory to save results')
    args = parser.parse_args()

    query = args.query
    crawl_type = args.crawl_type
    number = args.number
    dir_prefix = args.dir_prefix
    caption = args.caption

    crawler = InstagramCrawler()
    crawler.crawl(query=query, crawl_type=crawl_type, number=number, caption=caption, dir_prefix=dir_prefix)

if __name__ == "__main__":
    main()
