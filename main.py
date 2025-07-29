import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from rss_tracker import get_latest_video_from_rss
from youtube_downloader import download_audio_from_youtube
from transcribe_whisper import transcribe_audio
from summarize_gpt import summarize_text

# Load environment variables
load_dotenv()

# Constants
STATE_FILE = "state.json"
RSS_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id=PLZPgleW4baxpCtioKMLwGfWxeUUIuZi49"
DOWNLOAD_DIR = "downloads"
LOG_FILE = "run.log"

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_print(message):
    print(message)
    logging.info(message)

def log_error(message):
    print("❌", message)
    logging.error(message)

def load_last_video_id():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f).get("video_id")

def save_last_video_id(video_id):
    with open(STATE_FILE, "w") as f:
        json.dump({"video_id": video_id}, f)

def main():
    log_print("🔍 Checking for new episode...")
    try:
        video_id, title, url = get_latest_video_from_rss(RSS_URL)
    except Exception as e:
        log_error(f"Failed to fetch RSS: {e}")
        return

    last_video_id = load_last_video_id()
    if video_id == last_video_id:
        log_print("✅ No new episode.")
        return

    log_print(f"🆕 New episode found: {title}")
    try:
        mp3_path, safe_title = download_audio_from_youtube(url)
        log_print(f"🎧 Audio downloaded: {mp3_path}")
    except Exception as e:
        log_error(f"Download failed: {e}")
        return

    try:
        transcript = transcribe_audio(mp3_path)
        transcript_file = os.path.join(DOWNLOAD_DIR, f"{video_id}_transcript.txt")
        with open(transcript_file, "a", encoding="utf-8") as f:
            f.write(transcript)
        log_print(f"📝 Transcript saved to: {transcript_file}")
    except Exception as e:
        log_error(f"Transcription failed: {e}")
        return

    try:
        summary = summarize_text(transcript)
        summary_file = os.path.join(DOWNLOAD_DIR, f"{video_id}_summary.txt")
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)
        log_print(f"📌 Summary saved to: {summary_file}")
    except Exception as e:
        log_error(f"Summarization failed: {e}")
        return

    save_last_video_id(video_id)
    log_print("✅ Done.")

if __name__ == "__main__":
    main()
