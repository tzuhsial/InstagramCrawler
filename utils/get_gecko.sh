#!/bin/bash

# following travis.yml https://github.com/iammrhelo/InstagramCrawler/blob/master/.travis.yml#L11-L14

wget https://github.com/mozilla/geckodriver/releases/download/v0.16.0/geckodriver-v0.16.0-linux64.tar.gz
mkdir -p geckodriver && tar zxvf geckodriver-v0.16.0-linux64.tar.gz -C geckodriver

