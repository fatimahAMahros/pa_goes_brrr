# Scraping Comment
So far, [test_instagram.py](./test_instagram.py) can only scrape comments based off of post urls. The post urls  themselves were gotten from Apify's post scraper when I was trying their free plan.

The comment scraper itself is based on this [IG Exporter & Scraper chrome extension](https://chromewebstore.google.com/detail/nmgmcehdhckaehgfokcomaboclhbdpkb?utm_source=item-share-cb) but automated to handle batch urls.

### Cookies
To run it, make sure you have an active session of instagram login to utilize the cookies for this scraping. The cookies necessary for this to work are listed in the .env.example.
***Make sure to check once in a while that your cookies haven't expired or renewed with different values.***

### Randomized Sleep Duration
To reduce the possibility of getting detected as automated or getting rate limited while scraping, make sure that the duration of sleep between each requests are not too short and uniformed. This won't guarantee that you will be 100% be undetected, but it will help reduce the risk.
There are three main sleep duration:
- **Pagination sleep**: This will put a sleep between each pagination requests, since instagram will only load at most 50 comments in one request. This sleep shouldn't need too long of a duration, but 10 seconds is the recommended smallest amount.
- **Next Post Sleep**: This will put a sleep when changing from one url to another. There is no recommended sleep time, but a longer time than the duration for pagination is safer.
- **Sleep after n posts**: This will put a longer sleep between a group requests based on amount of post urls scraped, with the unit being minutes instead of seconds like the other sleeps. This is to also help reduce the possibility of getting detected as automated.

### IMPORTANT!! Number of Comments
The number of comments scraped using this script may differ from what is displayed on instagram, as instagram will also count the comments that are from Facebook, and those that are deleted.

### Proxy
You may need to configure a proxy if you have a bad IP reputation.