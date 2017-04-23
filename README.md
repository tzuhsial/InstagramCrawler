Feel free to open a Github issue if you have any problems running the code
---
# InstagramCrawler
A non API python program to crawl public photos, posts

### Example:
Download the first 100 photos and captions(user's posts, if any) from username "instagram"

NOTE: When I ran on public account 'instagram', somehow it stops at caption 29
```
$ python instagramcrawler.py -q 'instagram' -c -n 100
```
Search for the hashtag "#breakfast" and download first 50 photos
```
$ python instagramcrawler.py -q '#breakfast' -n 50
```

Record the first 30 followers of the username "instagram", requires log in
```
$ python instagramcrawler.py -q 'instagram' -t 'followers' -n 30
```

### Full usage:
```
usage: instagramcrawler.py [-h] [-q QUERY] [-n NUMBER] [-c] [-d DIR]
```
  - [-d DIR]: the directory to save crawling results, default is './data/[query]'
  - [-q QUERY] : username, add '#' to search for hashtags, e.g. 'username', '#hashtag'
  - [-t CRAWL_TYPE]: crawl_type, Options: 'photos | followers | following'
  - [-c]: add this flag to download captions(what user wrote to describe their photos)
  - [-n NUMBER]: number of posts, followers, or following to crawl,  


### Installation
There are 2 packages : selenium & requests

NOTE: I used selenium = 3.4, geckodriver = 0.16 (fixed bug in previous versions)
```
$ pip install -r requirements.txt
```
