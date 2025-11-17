import requests
import json
import time
import csv
import random
import re
import os
import sys
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv

class InstagramCommentScraper:
    def __init__(self, session_cookies=None):
        self.session = requests.Session()
        self.base_url = "https://www.instagram.com"
        self.query_hash = "33ba35852cb50da46f5b5e889df7d159"
        
        # Set comprehensive headers to mimic real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': '936619743392459',
            'Referer': 'https://www.instagram.com/',
        })
        
        if session_cookies:
            # Update session cookies
            for name, value in session_cookies.items():
                self.session.cookies.set(name, value)
    
    def check_critical_error(self, response, context=""):
        """Check for critical errors that should stop execution"""
        if response.status_code == 401:
            print(f"❌ CRITICAL ERROR: Authentication failed (401 Unauthorized) {context}")
            print("Your session cookies may have expired. Please update them.")
            return True
            
        elif response.status_code == 403:
            print(f"❌ CRITICAL ERROR: Access forbidden (403 Forbidden) {context}")
            print("Instagram has blocked your access. You may be rate limited or banned.")
            return True
            
        elif response.status_code == 429:
            print(f"❌ CRITICAL ERROR: Rate limited (429 Too Many Requests) {context}")
            print("You're being rate limited. Wait several hours before trying again.")
            return True
            
        elif response.status_code >= 500:
            print(f"❌ CRITICAL ERROR: Server error ({response.status_code}) {context}")
            print("Instagram servers are having issues. Try again later.")
            return True
            
        # Check for Instagram-specific error patterns in response
        try:
            data = response.json()
            if 'message' in data and any(error_msg in data['message'].lower() for error_msg in ['login', 'authenticate', 'blocked', 'suspended', 'banned']):
                print(f"❌ CRITICAL ERROR: Instagram returned error: {data['message']}")
                return True
        except:
            pass
            
        return False
    
    def extract_shortcode(self, post_url):
        """Extract shortcode from Instagram post URL"""
        patterns = [
            r'instagram\.com/p/([^/?]+)',
            r'instagram\.com/reel/([^/?]+)',
            r'instagram\.com/stories/[^/]+/([^/?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, post_url)
            if match:
                return match.group(1)
        
        parsed = urlparse(post_url)
        path_parts = parsed.path.strip('/').split('/')
        if path_parts and path_parts[-1]:
            return path_parts[-1]
        
        raise ValueError(f"Could not extract shortcode from URL: {post_url}")
    
    def get_comments(self, shortcode, after_cursor="", count=50):
        """Fetch comments from Instagram GraphQL API"""
        variables = {
            "shortcode": shortcode,
            "after": after_cursor,
            "first": count
        }
        
        params = {
            "query_hash": self.query_hash,
            "variables": json.dumps(variables, separators=(',', ':'))
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/graphql/query/",
                params=params,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            # Check for critical errors that should stop execution
            if self.check_critical_error(response, f"while fetching comments for post {shortcode}"):
                return None, True  # Return tuple with critical error flag
            
            # Check if response is JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                print(f"⚠️  Unexpected content type: {content_type}")
                print(f"Response text (first 500 chars): {response.text[:500]}")
                return None, False
            
            return response.json(), False
                
        except requests.RequestException as e:
            print(f"⚠️  Request failed: {e}")
            return None, False
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON decode error: {e}")
            print(f"Response text (first 500 chars): {response.text[:500]}")
            return None, False
    
    def parse_comments(self, data):
        """Parse comments from GraphQL response"""
        comments = []
        
        try:
            # Navigate through the GraphQL response structure
            shortcode_media = data.get('data', {}).get('shortcode_media', {})
            
            if not shortcode_media:
                print("No shortcode_media found in response")
                return [], False, ""
                
            # Use edge_media_to_comment instead of edge_media_to_parent_comment
            edge_media_to_comment = shortcode_media.get('edge_media_to_comment', {})
            edges = edge_media_to_comment.get('edges', [])
            
            print(f"Found {len(edges)} comment edges")
            
            for edge in edges:
                node = edge.get('node', {})
                comment = {
                    'comment_id': node.get('id'),
                    'text': node.get('text', ''),
                    'created_at': node.get('created_at'),
                    'user_id': node.get('owner', {}).get('id'),
                    'username': node.get('owner', {}).get('username'),
                    'profile_pic_url': node.get('owner', {}).get('profile_pic_url'),
                    'parent_comment_id': ''  # Top-level comments don't have parent
                }
                
                # Get replies if available (threaded comments)
                edge_threaded_comments = node.get('edge_threaded_comments', {})
                reply_edges = edge_threaded_comments.get('edges', [])
                
                # Add main comment
                comments.append(comment)
                
                # Add replies
                for reply_edge in reply_edges:
                    reply_node = reply_edge.get('node', {})
                    reply = {
                        'comment_id': reply_node.get('id'),
                        'text': reply_node.get('text', ''),
                        'created_at': reply_node.get('created_at'),
                        'user_id': reply_node.get('owner', {}).get('id'),
                        'username': reply_node.get('owner', {}).get('username'),
                        'profile_pic_url': reply_node.get('owner', {}).get('profile_pic_url'),
                        'parent_comment_id': node.get('id')  # Link to parent comment
                    }
                    comments.append(reply)
            
            # Get next page cursor
            page_info = edge_media_to_comment.get('page_info', {})
            has_next_page = page_info.get('has_next_page', False)
            end_cursor = page_info.get('end_cursor', '')
            
            return comments, has_next_page, end_cursor
            
        except Exception as e:
            print(f"⚠️  Error parsing comments: {e}")
            import traceback
            traceback.print_exc()
            return [], False, ""
    
    def scrape_all_comments(self, post_url, min_delay=23, max_delay=39):
        """Scrape all comments from a post with pagination and random delays"""
        shortcode = self.extract_shortcode(post_url)
        print(f"Scraping comments for post: {shortcode}")
        
        all_comments = []
        after_cursor = ""
        page = 1
        
        while True:
            print(f"Fetching page {page}...")
            
            data, critical_error = self.get_comments(shortcode, after_cursor)
            
            # If critical error occurred, stop execution
            if critical_error:
                return None, True
                
            if not data:
                print("Failed to fetch comments")
                break
            
            comments, has_next_page, end_cursor = self.parse_comments(data)
            
            # Add post_id to each comment
            for comment in comments:
                comment['post_id'] = shortcode
                comment['post_url'] = post_url
                comment['scraped_at'] = datetime.now().isoformat()
            
            all_comments.extend(comments)
            
            print(f"Page {page}: Found {len(comments)} comments")
            
            if not has_next_page:
                print("No more pages")
                break
            
            after_cursor = end_cursor
            page += 1
            
            # Random delay between requests (31-47 seconds)
            delay = random.randint(min_delay, max_delay)
            print(f"Waiting {delay} seconds before next request...")
            time.sleep(delay)
        
        print(f"Total comments scraped: {len(all_comments)}")
        return all_comments, False

def read_urls_from_csv(csv_file):
    """Read Instagram post URLs from CSV file"""
    urls = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'url' in row and row['url'].strip():
                    urls.append(row['url'].strip())
        print(f"Read {len(urls)} URLs from {csv_file}")
        return urls
    except FileNotFoundError:
        print(f"❌ CSV file {csv_file} not found")
        return []
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return []

def read_completed_urls(completed_file):
    """Read already completed URLs from file"""
    completed = set()
    try:
        with open(completed_file, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url:
                    completed.add(url)
        print(f"Found {len(completed)} completed URLs")
        return completed
    except FileNotFoundError:
        print(f"Completed URLs file {completed_file} not found, creating new one")
        return set()

def save_completed_url(completed_file, url):
    """Save completed URL to file"""
    try:
        with open(completed_file, 'a', encoding='utf-8') as f:
            f.write(url + '\n')
    except Exception as e:
        print(f"⚠️  Error saving completed URL: {e}")

def append_comments_to_csv(comments, csv_file):
    """Append comments to main CSV file"""
    if not comments:
        return
    
    fieldnames = ['post_id', 'post_url', 'comment_id', 'text', 'created_at', 'user_id', 
                  'username', 'profile_pic_url', 'parent_comment_id', 'scraped_at']
    
    file_exists = os.path.isfile(csv_file)
    
    try:
        with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                print(f"Created new CSV file: {csv_file}")
            
            for comment in comments:
                writer.writerow(comment)
        
        print(f"Appended {len(comments)} comments to {csv_file}")
        
    except Exception as e:
        print(f"❌ Error writing to CSV file: {e}")

def graceful_shutdown(message, exit_code=1):
    """Gracefully shutdown the script with an error message"""
    print(f"\n{'='*60}")
    print(f"❌ SCRIPT STOPPED: {message}")
    print(f"{'='*60}")
    sys.exit(exit_code)

def main():
    # Configuration
    URLS_CSV = "scrape_instagram/posts_with_comments.csv"  # Your CSV with URLs
    OUTPUT_CSV = "instagram_comments.csv"  # Single output file
    COMPLETED_FILE = "completed_urls.txt"  # Track completed URLs
    POSTS_BEFORE_BREAK = 10  # Break after every 7 posts
    BREAK_MIN_MINUTES = 5  # Minimum break duration in minutes
    BREAK_MAX_MINUTES = 11  # Maximum break duration in minutes

    load_dotenv()
    
    # Your Instagram cookies - replace with your actual cookies
    manual_cookies = {
        'sessionid': os.environ.get('SESSION_ID'),
        'ds_user_id': os.environ.get('DS_USER_ID'), 
        'csrftoken': os.environ.get('CSRF_TOKEN'),
        'rur': os.environ.get('RUR_COOKIE'),
        'mid': os.environ.get('MID_COOKIE')
    }
    
    # Remove the quotes from rur value if they exist
    if 'rur' in manual_cookies and manual_cookies['rur'].startswith('"'):
        manual_cookies['rur'] = manual_cookies['rur'].strip('"')
    
    # Initialize scraper with cookies
    scraper = InstagramCommentScraper(manual_cookies)
    
    # Test authentication
    print("Testing authentication...")
    try:
        test_response = scraper.session.get("https://www.instagram.com/", timeout=30)
        
        # Check for critical errors during authentication test
        if scraper.check_critical_error(test_response, "during authentication test"):
            graceful_shutdown("Authentication test failed with critical error")
            
        if test_response.status_code == 200:
            print("✓ Authentication successful")
        else:
            print(f"⚠️  Authentication test returned status: {test_response.status_code}")
            
    except requests.RequestException as e:
        graceful_shutdown(f"Authentication test failed: {e}")
    
    # Read URLs and completed URLs
    all_urls = read_urls_from_csv(URLS_CSV)
    completed_urls = read_completed_urls(COMPLETED_FILE)
    
    if not all_urls:
        graceful_shutdown("No URLs found to process")
    
    # Filter out already completed URLs
    urls_to_process = [url for url in all_urls if url not in completed_urls]
    
    if not urls_to_process:
        print("All URLs have already been processed")
        sys.exit(0)
    
    print(f"Processing {len(urls_to_process)} URLs (skipping {len(completed_urls)} already completed)")
    
    # Process each URL
    for i, post_url in enumerate(urls_to_process):
        print(f"\n{'='*60}")
        print(f"Processing post {i+1}/{len(urls_to_process)}")
        print(f"URL: {post_url}")
        print(f"{'='*60}")
        
        try:
            # Scrape with random delays between requests (31-47 seconds)
            comments, critical_error = scraper.scrape_all_comments(post_url, min_delay=23, max_delay=39)
            
            # If critical error occurred during scraping, stop execution
            if critical_error:
                graceful_shutdown("Critical error encountered during comment scraping")
            
            if comments:
                # Append to main CSV file
                append_comments_to_csv(comments, OUTPUT_CSV)
                print(f"✓ Successfully processed: {post_url}")
            else:
                print(f"⚠️  No comments found for: {post_url}")
            
            # Mark as completed
            save_completed_url(COMPLETED_FILE, post_url)
            completed_urls.add(post_url)
            
            # Check if we need to take a break
            if (i + 1) % POSTS_BEFORE_BREAK == 0 and (i + 1) < len(urls_to_process):
                break_minutes = random.randint(BREAK_MIN_MINUTES, BREAK_MAX_MINUTES)
                break_seconds = break_minutes * 60
                print(f"\n{'='*60}")
                print(f"Completed {POSTS_BEFORE_BREAK} posts. Taking a break for {break_minutes} minutes...")
                print(f"{'='*60}")
                time.sleep(break_seconds)
                print("Break finished, resuming...")
            
            # Random delay between posts (31-47 seconds)
            if i < len(urls_to_process) - 1:
                delay = random.randint(31, 47)
                print(f"Waiting {delay} seconds before next post...")
                time.sleep(delay)
                
        except KeyboardInterrupt:
            print(f"\n{'='*60}")
            print("Script interrupted by user")
            print(f"Successfully processed {i} posts")
            print(f"Resume by running the script again")
            print(f"{'='*60}")
            sys.exit(0)
            
        except Exception as e:
            print(f"⚠️  Error processing {post_url}: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if it's a critical exception that should stop execution
            if isinstance(e, (requests.RequestException, ConnectionError, TimeoutError)):
                print("⚠️  Network error encountered, but continuing...")
            
            # Continue with next URL even if one fails (unless it's a critical error)
            if i < len(urls_to_process) - 1:
                delay = random.randint(31, 47)
                print(f"Waiting {delay} seconds before next post...")
                time.sleep(delay)
    
    print("\n" + "="*60)
    print("🎉 Scraping completed successfully!")
    print(f"Processed {len(urls_to_process)} posts")
    print(f"Output saved to: {OUTPUT_CSV}")
    print(f"Completed URLs tracked in: {COMPLETED_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()