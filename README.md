# InstagramCrawler
---
A selenium based python brute force non-api crawler to crawl public photos, posts or followers <br/>
Borrowed a lot from [InstaRaider](https://github.com/akurtovic/InstaRaider)
##### Example:
This command downloads 100 photos from the account "instagram" and also their captions
```
  python instagramcrawler.py -q instagram -t photos -c -n 100
```
### Full usage:
```
  usage: instagramcrawler.py [-h] [-q QUERY] [-t TYPE] [-n NUMBER] [-c] [-d DIR]
```
Flags:
  - [-q QUERY] : username, add '#' to search for hashtags
  - [-t TYPE] : specify 'photos','followers' or 'following'
  - [-c]: add this flag to download captions(what user write on their posts) if TYPE is 'photos'
  - [-n NUMBER]: number or posts or followers to crawl,  
  - [-d DIR]: the directory to save crawling results, default is './data/'


### Installation

  There are 2 packages : selenium & requests-futures
```
  pip install -r requirements.txt
```
