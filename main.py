import os
from pathlib import Path
from dotenv import load_dotenv
from utils import *
# Load environment variables
load_dotenv()

# Constants
RSS_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id=PLZPgleW4baxpCtioKMLwGfWxeUUIuZi49"
DOWNLOAD_DIR = "downloads"




def main(steps):

    if "All" in steps:
        steps = ["Check", "Download", "Transcribe", "Summarize", "Tweet"]

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
        video_id, title, url = "test_video_id", "פרק 192 - שמן משווארמה בבת מצווה בפסאז׳ | הקרנף", "test_url"

    if "Download" in steps:
        log(f"New episode found: {title}")
        try:
            mp3_path, _ = download_audio_from_youtube(url)
            log(f"Audio downloaded: {mp3_path}")
        except Exception as e:
            log(f"Download failed: {e}")
            return
    else:
        mp3_path = os.path.join("test_files", "test_episode.mp3")
        log("Skipping download step.")
        log(f"Using test file: {mp3_path}")

    if "Transcribe" in steps and mp3_path:
        try:
            transcript = transcribe_audio(mp3_path)
            # add the episode title to the transcript beginning
            transcript = f"Episode Title: {title}\n\n{transcript}"
            transcript_file = os.path.join(DOWNLOAD_DIR, f"{video_id}_transcript.txt")
            with open(transcript_file, "a", encoding="utf-8") as f:
                f.write(transcript)
            log(f"Transcript saved to: {transcript_file}")
        except Exception as e:
            log(f"Transcription failed: {e}", level="error")
            return
    else:
        log("Skipping transcription step.")
        log("Using test transcript file.")
        transcript_file = os.path.join("test_files", "test_transcript.txt")


    if "Summarize" in steps and transcript_file:
        try:
            summary = summarize_transcript_file(transcript_file)
            summary_file = os.path.join(DOWNLOAD_DIR, f"{video_id}_summary.txt")
            with open(summary_file, "w", encoding="utf-8") as out:
                out.write(repr(summary))
        except Exception as e:
            log(f"Summarization failed: {e}")
            return
    else:
        
        # time.sleep(10)  # Simulate a delay for the summarization step
        log("Skipping summarization step.")
        log("Using test summary file.")
        # summary_file = r"downloads\WLhTVaZO7oQ_summary.txt"

        summary_file = os.path.join("test_files", "test_summary.txt")
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = ast.literal_eval(f.read())
            
    if "Tweet" in steps and summary:
        try:
            status = post_tweets(summary)
            if status:
                log("Tweets posted successfully.")
            else:
                log("Failed to post tweets.")
        except Exception as e:
            log(f"Tweeting failed: {e}")
            

    save_last_video_id(video_id)
    log("Done.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Daily Karnaf Script")
    
    steps = [
        "All",
    ]
    main(steps)
