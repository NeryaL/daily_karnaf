import json
import dotenv
import os
import ast
import tiktoken

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

import openai

import feedparser
import yt_dlp
from typing import List

from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile

import re


dotenv.load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=API_KEY)


LOG_FILE = "run.log"
MAX_SIZE_BYTES = 25 * 1024 * 1024  # Whisper limit: 25MB
CHUNK_DURATION_MS = 60 * 1000      # 1 minute chunks


MODEL = "gpt-4o"
MAX_CONTEXT = 128_000
MAX_OUTPUT = 4000

# Prompt tailored for your use-case
PROMPT_INSTRUCTIONS = (
    "You are a professional summarizer. You will receive a transcript of a daily news podcast in Hebrew.\n"
    "Your task:\n"
    "- Summarize the entire content into 2–4 short Hebrew tweets.\n"
    "- the first tweet should include the yoav rabinovitch's x user handle: @yoavr above all\n"
    "- the first tweet should include the episode number and title.\n"
    "- you should focus on the author ideas and arguments, not the ones he cites.\n"
    "- Each tweet must be a complete, central, and coherent argument.\n"
    "- Each tweet must not exceed 200 characters.\n"
    "- Pay careful attention to sarcasm, irony, cynicism, and complex arguments.\n"
    "- Any reference to the host should be written as 'הקרנף' instead of using their real name (e.g., יואב רבינוביץ).\n"
    "- Format the output exactly as:\n"
    "  [\"point1…\", \"point2…\", \"point3…\"]\n"
    "- Do not include emojis or any extra characters.\n"
    "- Return only that JSON-style list, nothing else."
)

def count_tokens(text: str, model_name: str = MODEL) -> int:
    """Returns the number of tokens used by the input text with the specified model."""
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(text))

def summarize_full_context(transcript: str) -> list:
    """Send the full transcript and prompt together as a single context to the model."""
    transcript_tokens = count_tokens(transcript)
    prompt_tokens = count_tokens(PROMPT_INSTRUCTIONS)

    total_tokens = transcript_tokens + prompt_tokens
    if total_tokens >= MAX_CONTEXT:
        raise ValueError(f"Transcript too long: {total_tokens} tokens (limit is {MAX_CONTEXT})")

    available_for_output = min(MAX_CONTEXT - total_tokens, MAX_OUTPUT)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT_INSTRUCTIONS},
            {"role": "user", "content": transcript}
        ],
        temperature=0.3,
        max_tokens=available_for_output
    )
    raw_output = response.choices[0].message.content.strip()
    return ast.literal_eval(raw_output)

def summarize_transcript_file(input_path: str, output_path: str = "summary.txt"):
    """Main function: reads file, verifies size, summarizes, saves and prints output."""
    with open(input_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    summary = summarize_full_context(transcript)

    return summary


def log(message, level="info"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    text = f"{timestamp} [{level.upper()}] {message}"
    print(text)
    #save to log file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def post_tweets(tweets_list):
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
        if not tweets_list:
            log("No tweets provided in the list.")
            return
        
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
            log("Waiting for 3 seconds before attempting to post...")
            time.sleep(3)

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

            wait = WebDriverWait(driver, 10)

            # Locate tweet <article> by text content
            tweet_article = wait.until(EC.presence_of_element_located(
                (By.XPATH, f"//article[.//span[text()='{reply_text}']]")
            ))

            # Find the <a> tag inside that article which links to the tweet
            link_element = tweet_article.find_element(By.XPATH, ".//a[contains(@href, '/status/')]")
            current_tweet_url = link_element.get_attribute("href")

            print(f"Reply URL: {current_tweet_url}")



    except Exception as e:
        log(f"An error occurred: {e}", level="error")

    finally:
        driver.quit()
    

def split_audio_to_chunks(mp3_path: str, chunk_duration_ms: int) -> List[str]:
    """Splits MP3 into multiple temp files, returns list of paths."""
    audio = AudioSegment.from_file(mp3_path)
    chunks = []
    for i in range(0, len(audio), chunk_duration_ms):
        chunk = audio[i:i + chunk_duration_ms]
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        chunk.export(temp_file.name, format="mp3")
        chunks.append(temp_file.name)
    return chunks

def transcribe_chunk(chunk_path: str, index: int):
    """Transcribe a single audio chunk."""
    try:
        with open(chunk_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        return index, response
    finally:
        os.remove(chunk_path)  # Clean up

def transcribe_audio(mp3_path: str) -> str:
    file_size = os.path.getsize(mp3_path)
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if file_size <= MAX_SIZE_BYTES:
        log(f"Transcribing full file: {mp3_path}")
        with open(mp3_path, "rb") as audio_file:
            return client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

    log(f"File too large ({file_size} bytes), splitting and transcribing in parallel...")

    chunks = split_audio_to_chunks(mp3_path, CHUNK_DURATION_MS)
    results = [None] * len(chunks)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(transcribe_chunk, chunk, i) for i, chunk in enumerate(chunks)]
        for future in as_completed(futures):
            i, text = future.result()
            results[i] = text

    return "\n".join(results).strip()


def get_latest_video_from_rss(rss_url):
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        raise ValueError("No videos found in RSS feed")
    
    latest = feed.entries[0]
    video_id = latest['yt_videoid']
    title = latest['title']
    link = latest['link']
    
    return video_id, title, link


def download_audio_from_youtube(youtube_url: str, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        title = info['title']
        filename = os.path.join(output_dir, f"{info['id']}.mp3")
        return filename, title
    
def load_last_video_id(state_file="state.json"):
    if not os.path.exists(state_file):
        return None
    with open(state_file, "r") as f:
        return json.load(f).get("video_id")

def save_last_video_id(video_id, state_file="state.json"):
    with open(state_file, "w") as f:
        json.dump({"video_id": video_id}, f)


def extract_episode_number(title: str) -> int:
    match = re.search(r"פרק\s+(\d+)", title)
    if match:
        return int(match.group(1))
    raise ValueError("Episode number not found in title.")

if __name__ == "__main__":
    tweet_list = [
        "This is the first tweet.",
        "This is the second tweet.",
        "This is the third tweet."
    ]
    post_tweets(tweet_list)
