Feel free to open a Github issue if you have any problems running the code
---
# InstagramCrawler
A non API python program to crawl public photos, posts, followers, and following

##### Login to crawl followers/following
To crawl followers or followings, you will need to login with your credentials either by filling in 'auth.json' or typing in(as you would do when you are simply browsing instagram)

Well, it is to copy 'auth.json.example' to 'auth.json' and fill in your username and password

##### PhantomJS for headless browser
For headless browser, after installing [phantomjs](http://phantomjs.org/), add '-l' to the arguments

### Examples:
Download the first 100 photos and captions(user's posts, if any) from username "instagram"

###### NOTE: When I ran on public account 'instagram', somehow it stops at caption 29
```
$ python instagramcrawler.py -q 'instagram' -c -n 100
```
Search for the hashtag "#breakfast" and download first 50 photos
```
$ python instagramcrawler.py -q '#breakfast' -n 50
```
Record the first 30 followers of the username "instagram", requires log in
```
$ python instagramcrawler.py -q 'instagram' -t 'followers' -n 30 -a auth.json
```

### Full usage:
```
usage: instagramcrawler.py [-h] [-d DIR] [-q QUERY] [-t CRAWL_TYPE] [-n NUMBER] [-c]  [-a AUTHENTICATION]
```
  - [-d DIR]: the directory to save crawling results, default is './data/[query]'
  - [-q QUERY] : username, add '#' to search for hashtags, e.g. 'username', '#hashtag'
  - [-t CRAWL_TYPE]: crawl_type, Options: 'photos | followers | following'
  - [-n NUMBER]: number of posts, followers, or following to crawl
  - [-c]: add this flag to download captions(what user wrote to describe their photos)
  - [-a AUTHENTICATION]: path to a json file, which contains your instagram credentials, please see 'auth.json'
  - [-l HEADLESS]: If set, will use PhantomJS driver to run script as headless
  - [-f FIREFOX_PATH]: path to the **binary** (not the script) of firefox on your system (see this issue in Selenium https://github.com/SeleniumHQ/selenium/issues/3884#issuecomment-296988595)


### Installation
There are 2 packages : selenium & requests

###### NOTE: I used selenium = 3.4, geckodriver = 0.16 (fixed bug in previous versions)
```
$ pip install -r requirements.txt
```

###### Optional: geckodriver and phantomjs if not present on your system
```
bash utils/get_gecko.sh
bash utils/get_phantomjs.sh
source utils/set_path.sh
```

