echo "Check photos & captions..."
echo "Download first 10 photos and captions of account 'instagram'"
python instagramcrawler.py -q 'instagram' -n 20 -c

echo "Check hashtag..."
echo "Search for hashtag '#breakfast' and download 20 photos"
python instagramcrawler.py -q '#breakfast' -n 20
