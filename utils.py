
import dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Load environment variables
dotenv.load_dotenv()

def post_tweet(tweets_list):
# Initialize the WebDriver (e.g., Chrome)
    TWITTER_MAIL_ADDRESS = dotenv.get_key("TWITTER_MAIL_ADDRESS")
    TWITTER_PASSWORD = dotenv.get_key("TWITTER_PASSWORD")
    driver = webdriver.Chrome() # Ensure you have chromedriver installed and in your PATH
    
    try:
        driver.get("https://twitter.com/login")

        # Wait for login elements to be present and fill credentials
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "text"))).send_keys(TWITTER_MAIL_ADDRESS)
        driver.find_element(By.XPATH, "//span[text()='Next']").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(TWITTER_PASSWORD)
        driver.find_element(By.XPATH, "//span[text()='Log in']").click()

        # Wait for the home page to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']")))

        # Compose and post the tweet
        tweet_text = "Hello from Python without the X API!"
        driver.find_element(By.XPATH, "//div[@data-testid='tweetTextarea_0']").send_keys(tweet_text)
        driver.find_element(By.XPATH, "//span[text()='Post']").click() # Attempt to find 'Post' button
        # If the above fails, you might need to inspect the element on the live site
        # and update the XPath accordingly. Common alternatives include:
        # driver.find_element(By.XPATH, "//span[text()='Tweet']").click()
        # driver.find_element(By.CSS_SELECTOR, "[data-testid='tweetButton']").click() # If data-testid changes

        print("Tweet posted successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()