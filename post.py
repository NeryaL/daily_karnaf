
import dotenv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time

# Load environment variables
dotenv.load_dotenv()

def post_tweet(tweets_list):
    TWITTER_MAIL_ADDRESS = os.getenv("TWITTER_MAIL_ADDRESS")
    TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
    TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
    driver = webdriver.Chrome() # Ensure you have chromedriver installed and in your PATH

    try:
        driver.get("https://twitter.com/login")

        # Wait for login elements to be present and fill credentials
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "text"))).send_keys(TWITTER_MAIL_ADDRESS)
        driver.find_element(By.XPATH, "//span[text()='Next']").click()
        
        # Twitter may ask for username or password. We try for password field first.
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(TWITTER_PASSWORD)
        except:
            # if password is not there, it may ask for username
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "text"))).send_keys(TWITTER_USERNAME)
            driver.find_element(By.XPATH, "//span[text()='Next']").click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(TWITTER_PASSWORD)

        driver.find_element(By.XPATH, "//span[text()='Log in']").click()

        # Wait for the home page to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']")))

        # Post the first tweet
        if tweets_list:
            first_tweet_text = tweets_list[0]
            driver.find_element(By.XPATH, "//div[@data-testid='tweetTextarea_0']").send_keys(first_tweet_text)
            driver.find_element(By.XPATH, "//span[text()='Post']").click()
            print(f"Posted initial tweet: {first_tweet_text}")

            # Wait for the tweet to be posted and get its URL
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[text()='Your post was sent.']")))
            time.sleep(3)  # Give it a moment to settle
            
            profile_url = f"https://x.com/{TWITTER_USERNAME}"
            driver.get(profile_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//article")))
            
            # Find the link to the latest tweet
            tweet_link = driver.find_element(By.XPATH, "//article//a[contains(@href, '/status/')]")
            current_tweet_url = tweet_link.get_attribute('href')
            print(f"Initial tweet URL: {current_tweet_url}")


            # Iterate through the rest of the tweets as replies
            for i, reply_text in enumerate(tweets_list[1:]):
                print(f"Attempting to reply with: {reply_text}")
                # Navigate to the previous tweet's permalink to reply
                driver.get(current_tweet_url)

                # Wait for the reply input field to be present on the tweet page and type the reply
                reply_textarea_xpath = "//div[@data-testid='tweetTextarea_0']"
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, reply_textarea_xpath))).send_keys(reply_text)

                # Wait for a while before trying to send.
                print("Waiting for 5 seconds before attempting to post...")
                time.sleep(5)

                # The button text can be "Post" or "Reply". We find all matching elements and click the last one.
                buttons = driver.find_elements(By.XPATH, "//span[text()='Post' or text()='Reply']")
                if buttons:
                    buttons[-1].click()
                    print(f"Posted reply: {reply_text}")
                else:
                    raise Exception("Could not find post/reply button.")

                # Wait for the reply to be posted
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[text()='Your post was sent.']")))
                time.sleep(3)  # Give it a moment to settle

                # After replying, we need to find the URL of our new reply to continue the chain.
                # We can go to the user's profile and get the latest tweet's URL.
                profile_url = f"https://x.com/{TWITTER_USERNAME}"
                driver.get(profile_url)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//article")))
                
                # Find the link to the latest tweet (which is our reply)
                tweet_link = driver.find_element(By.XPATH, "//article//a[contains(@href, '/status/')]")
                current_tweet_url = tweet_link.get_attribute('href')
                print(f"Reply URL: {current_tweet_url}")

        else:
            print("No tweets provided in the list.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()
        
if __name__ == "__main__":
    # Example usage
    tweets = [
        "זהו ציוץ ראשון מתוך שרשור (בלי אימוג'ים בבקשה)",
        "והנה הציוץ השני בסדרה החשובה הזאת.",
        "וכמובן – איך אפשר בלי ציוץ שלישי לסיום השרשור."
    ]
    post_tweet(tweets)