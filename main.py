import os
import json
import logging

from dotenv import load_dotenv
from utils import *
# Load environment variables
load_dotenv()

# Constants
RSS_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id=PLZPgleW4baxpCtioKMLwGfWxeUUIuZi49"
DOWNLOAD_DIR = "downloads"
LOG_FILE = "run.log"




def main(steps):
    
    log(f"Starting daily karnaf script with steps: {', '.join(steps)}")
    
    
    if "Check" in steps:
        log("Checking for new episode...")
        try:
            video_id, title, url = get_latest_video_from_rss(RSS_URL)
        except Exception as e:
            log(f"Failed to fetch RSS: {e}")
            return

        last_video_id = load_last_video_id()
        if video_id == last_video_id:
            log("No new episode.")
            return
    else:
        log("Skipping check for new episode.")
        video_id, title, url = None, None, None
    
    if "Download" in steps:
        log(f"New episode found: {title}")
        try:
            mp3_path, safe_title = download_audio_from_youtube(url)
            log(f"Audio downloaded: {mp3_path}")
        except Exception as e:
            log(f"Download failed: {e}")
            return
    else:
        log("Skipping download step.")
        mp3_path, safe_title = None, None
    
    if "Transcribe" in steps and mp3_path:
        try:
            transcript = transcribe_audio(mp3_path)
            transcript_file = os.path.join(DOWNLOAD_DIR, f"{video_id}_transcript.txt")
            with open(transcript_file, "a", encoding="utf-8") as f:
                f.write(transcript)
            log(f"Transcript saved to: {transcript_file}")
        except Exception as e:
            log(f"Transcription failed: {e}", level="error")
            return
    else:
        log("Skipping transcription step.")
        transcript = None
    
    if "Summarize" in steps and transcript:
        try:
            summary = summarize_transcript_file(transcript)
            summary_file = os.path.join(DOWNLOAD_DIR, f"{video_id}_summary.txt")
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(summary)
            log(f"Summary saved to: {summary_file}")
        except Exception as e:
            log(f"Summarization failed: {e}")
            return
    else:
        log("Skipping summarization step.")
        summary = None
        
    if "Tweet" in steps and summary:
        try:
            post_tweets(summary)
            log("Tweets posted successfully.")
        except Exception as e:
            log(f"Tweeting failed: {e}")
            return

    save_last_video_id(video_id)
    log("Done.")

if __name__ == "__main__":
    
    steps = [
        "Check",
        "Download",
        "Transcribe",
        "Summarize",
        "Tweet",
    ]
    main(steps)
