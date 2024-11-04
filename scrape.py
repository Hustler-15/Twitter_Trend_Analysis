import time
from googletrans import Translator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from transliterate import translit
import pandas as pd
import urllib.parse
import re


driver = webdriver.Chrome()

# Function to log in to Twitter
def login_to_twitter(username, password, phone):
    driver.get("https://twitter.com/login")
    time.sleep(3)  # Wait for the login page to load

    # Enter username
    username_input = driver.find_element(By.NAME, "text")
    username_input.send_keys(username)
    username_input.send_keys(Keys.RETURN)
    time.sleep(3)  # Wait for the next page to load

    # Enter number if asked
    username_input = driver.find_element(By.NAME, "text")
    username_input.send_keys(phone)
    username_input.send_keys(Keys.RETURN)
    time.sleep(3)  # Wait for the next page to load

    # Enter password
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)
    time.sleep(5)  # Wait for the home page to load

# Function to scrape trending topics
def scrape_and_save_trending_hashtags(filename="trending_hashtags.txt"):
    driver.get("https://twitter.com/explore/tabs/trending")
    time.sleep(5)  # Allow time for page elements to load

    # Scroll to ensure content is loaded
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    # Locate trending elements
    trending = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="trend"]')

    if not trending:
        print("No trending topics found. Check selectors or page structure.")
        return

    trends_data = []
    for trend in trending[:30]:  # Limit to top 30 trends
        try:
            # Find the span that contains the actual trend text
            trend_text_element = trend.find_elements(By.CSS_SELECTOR, 'span')
            trend_text = trend_text_element[3].text.strip()
            print(trend.get_attribute('outerHTML'))
            print(f"Raw trend text: '{trend_text}'")  # Debug output
            
            # Validate and filter the trend text
            if trend_text and not trend_text.isdigit() and trend_text != ".":
                trends_data.append(trend_text)
                print(f"Found trend: {trend_text}")
        except Exception as e:
            print("Error retrieving trend text:", e)

    # Write the trends to a text file
    if trends_data:
        with open(filename, "w", encoding="utf-8") as file:
            for trend in trends_data:
                file.write(f"{trend}\n")
                print(f"Writing trend to file: {trend}")
        print(f"Top 30 trending hashtags saved to {filename}")
    else:
        print("No data collected to write to file.")
    return trends_data    

# Function to scrape tweets for a specific trend
def scrape_tweets_for_hashtag(hashtag, max_tweets=3000):
    # URL-encode the hashtag for proper handling of special characters
    encoded_hashtag = urllib.parse.quote_plus(f"#{hashtag}")
    driver.get(f"https://twitter.com/search?q={encoded_hashtag}&f=top")
    time.sleep(5)  # Wait for the tweets to load

    tweets_data = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(tweets_data) < max_tweets:
        # Collect the tweets currently loaded
        tweets = driver.find_elements(By.XPATH, '//article')
        
        # Iterate through the loaded tweets
        for tweet in tweets:
            tweet_content = tweet.text
            try:
                username = tweet.find_element(By.XPATH, './/span[contains(text(),"@")]').text  # Extract username
                created_at = tweet.find_element(By.XPATH, './/time').get_attribute('datetime')  # Extract timestamp
                
                # Extract retweet, like, reply, and quote counts, with a fallback to 0
                retweet_count = tweet.find_element(By.XPATH, './/div[@data-testid="retweet"]').text if tweet.find_elements(By.XPATH, './/div[@data-testid="retweet"]') else "0"
                like_count = tweet.find_element(By.XPATH, './/div[@data-testid="like"]').text if tweet.find_elements(By.XPATH, './/div[@data-testid="like"]') else "0"
                reply_count = tweet.find_element(By.XPATH, './/div[@data-testid="reply"]').text if tweet.find_elements(By.XPATH, './/div[@data-testid="reply"]') else "0"
                quote_count = tweet.find_element(By.XPATH, './/div[@data-testid="quote"]').text if tweet.find_elements(By.XPATH, './/div[@data-testid="quote"]') else "0"
                
                # Placeholder values for geo_location, source, user_followers_count, and user_verified
                geo_location = "Not available"  # Replace with actual logic if you want to capture geo info
                source = "Twitter Web"  # Placeholder, you may want to refine this based on actual tweet source
                user_followers_count = "Not available"  # Replace with logic to get user followers count
                user_verified = False  # Replace with logic to check if user is verified
                
                tweets_data.append({
                    'username': username,
                    'tweet_content': tweet_content,
                    'created_at': created_at,
                    'retweet_count': retweet_count,
                    'like_count': like_count,
                    'reply_count': reply_count,
                    'quote_count': quote_count,
                    'hashtag': f"#{hashtag}",
                    'language': "Not available",  # Placeholder for language detection
                    'geo_location': geo_location,
                    'source': source,
                    'user_followers_count': user_followers_count,
                    'user_verified': user_verified,
                    'url': f"https://twitter.com/{username}/status/{tweet.get_attribute('data-tweet-id')}"  # Construct tweet URL
                })
                
                # Stop if we've reached the desired number of tweets
                if len(tweets_data) >= max_tweets:
                    break

            except Exception as e:
                print("Error processing tweet:", e)

        # Scroll down to load more tweets
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(7)  # Wait for new tweets to load

        # Calculate new scroll height and compare with last height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # If no new tweets are loaded, stop
            break
        last_height = new_height

    return tweets_data

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Data saved to {filename}")

def transliterate_to_english(text):
    translator = Translator()
    try:
        # Detect the language of the input text
        detected = translator.detect(text)
        lang_code = detected.lang
        
        # Translate the text to English
        transliterated_text = translator.translate(text, dest='en', src=lang_code).text
        
        return transliterated_text
    except Exception as e:
        print("Error during transliteration:", e)
        return None

# Replace with your Twitter username and password
username = "Hustler_644531"
password = "badeloghkrtehonge"
phone = "9372691221"

# Log in to Twitter
login_to_twitter(username, password, phone)

# Scrape trending topics
trending_topics = scrape_and_save_trending_hashtags()
print("Trending Topics:")
for hashtag in trending_topics:
    print(f"Trend: {hashtag}" )

    # Scrape tweets for the hashtag
    tweets_data = scrape_tweets_for_hashtag(hashtag, max_tweets=100)

    # Save tweets data to CSV
    save_to_csv(tweets_data, f"data\\{transliterate_to_english(hashtag)}_tweets.csv")

# Close the WebDriver
driver.quit()

