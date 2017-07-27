echo "Query account 'instagram', download 20 photos and their captions"
python instagramcrawler.py -q 'instagram' -n 20 -c

echo "Query hashtag '#breakfast' and download 20 photos"
python instagramcrawler.py -q '#breakfast' -n 20
