# InstagramCrawler
A non API python program to crawl public photos, posts or followers.  
Borrowed a lot from [InstaRaider](https://github.com/akurtovic/InstaRaider).
### Example:

Download the first 100 photos and captions(user's posts, if any) from username "instagram"
```
$ python instagramcrawler.py -q 'instagram' -t 'photos' -c -n 100
```

Search for the hashtag "#breakfast" and download first 50 photos
```
$ python instagramcrawler.py -q '#breakfast' -t 'photos' -n 50
```

Record the first 300 followers of the username "instagram", requires log in
```
$ python instagramcrawler.py -q 'instagram' -t 'followers' -n 300
```

### Full usage:
```
  usage: instagramcrawler.py [-h] [-q QUERY] [-t TYPE] [-n NUMBER] [-c] [-d DIR]
```
  - [-q QUERY] : username, add '#' to search for hashtags, e.g. 'username', '#hashtag'
  - [-t TYPE] : specify 'photos','followers' or 'following'
  - [-c]: add this flag to download captions(what user wrote to describe their photos) if TYPE is 'photos'
  - [-n NUMBER]: number of posts, followers, or following to crawl,  
  - [-d DIR]: the directory to save crawling results, default is './data/[query]'

### Installation

  There are 2 packages : selenium & requests-futures
```
$ pip install -r requirements.txt
```
