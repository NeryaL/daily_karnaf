import os
from pathlib import Path
from dotenv import load_dotenv
from utils import *
from send_mail import send_email
import datetime
import traceback
import ast

# Load environment variables
load_dotenv()

# Constants
RSS_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id=PLZPgleW4baxpCtioKMLwGfWxeUUIuZi49"
ARTIFACTS_DIR = "artifacts"

def main(steps, is_docker):
    run_status = "SUCCESS"
    
    # Setup run-specific artifacts directory and log file
    run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_artifact_dir = os.path.join(ARTIFACTS_DIR, f"run_{run_timestamp}")
    os.makedirs(run_artifact_dir, exist_ok=True)
    
    run_log_file = os.path.join(run_artifact_dir, "run.log")
    set_log_file(run_log_file)

    try:
        log(f"Starting daily karnaf script with steps: {', '.join(steps)}")
        log(f"Using docker: {is_docker}")
        log(f"Artifacts directory: {run_artifact_dir}")
    
        if "All" in steps:
            steps = ["Check", "Download", "Transcribe", "Summarize", "Tweet"]

        if "Check" in steps:
            log("Checking for new episode...")
            try:
                video_id, title, url = get_latest_video_from_rss(RSS_URL)
            except Exception as e:
                log(f"Failed to fetch RSS: {e}")
                raise

            last_video_id = load_last_video_id()
            if video_id == last_video_id:
                log("No new episode.")
                run_status = "NO_NEW_EPISODE"
                return
        else:
            log("Skipping check for new episode.")
            video_id, title, url = "test_video_id", "פרק 192 - שמן משווארמה בבת מצווה בפסאז׳ | הקרנף", "test_url"

        if "Download" in steps:
            log(f"New episode found: {title}")
            try:
                mp3_path, _ = download_audio_from_youtube(url, output_dir=run_artifact_dir)
                log(f"Audio downloaded: {mp3_path}")
            except Exception as e:
                log(f"Download failed: {e}")
                raise
        else:
            mp3_path = os.path.join("test_files", "test_episode.mp3")
            log("Skipping download step.")
            log(f"Using test file: {mp3_path}")

        if "Transcribe" in steps and mp3_path:
            try:
                transcript = transcribe_audio(mp3_path)
                transcript = f"Episode Title: {title}\n\n{transcript}"
                transcript_file = os.path.join(run_artifact_dir, f"{video_id}_transcript.txt")
                with open(transcript_file, "a", encoding="utf-8") as f:
                    f.write(transcript)
                log(f"Transcript saved to: {transcript_file}")
            except Exception as e:
                log(f"Transcription failed: {e}", level="error")
                raise
        else:
            log("Skipping transcription step.")
            log("Using test transcript file.")
            transcript_file = os.path.join("test_files", "test_transcript.txt")

        if "Summarize" in steps and transcript_file:
            try:
                summary = summarize_transcript_file(transcript_file)
                summary_file = os.path.join(run_artifact_dir, f"{video_id}_summary.txt")
                with open(summary_file, "w", encoding="utf-8") as out:
                    out.write(repr(summary))
            except Exception as e:
                log(f"Summarization failed: {e}")
                raise
        else:
            log("Skipping summarization step.")
            log("Using test summary file.")
            summary_file = os.path.join("test_files", "test_summary.txt")
            with open(summary_file, "r", encoding="utf-8") as f:
                summary = ast.literal_eval(f.read())
                
        if "Tweet" in steps and summary:
            try:
                status = post_tweets(summary, is_docker)
                if status:
                    log("Tweets posted successfully.")
                else:
                    log("Failed to post tweets.")
            except Exception as e:
                log(f"Tweeting failed: {e}")
                raise
                
        save_last_video_id(video_id)
        log("Done.")

    except Exception as e:
        run_status = "FAILURE"
        error_message = f"An error occurred: {e}\n{traceback.format_exc()}"
        log(error_message, level="error")
    finally:
        subject = f"Daily Karnaf Run Report: {run_status}"
        log_contents = ""
        if os.path.exists(run_log_file):
            with open(run_log_file, 'r', encoding='utf-8') as f:
                log_contents = f.read()
        
        send_email(subject, log_contents)
        log(f"Email notification sent for run status: {run_status}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Daily Karnaf Script")
    parser.add_argument('--docker', action='store_true', help='Run in Docker container')
    args = parser.parse_args()
    
    steps = ["All"]
    main(steps, args.docker)