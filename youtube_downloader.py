import yt_dlp
import os

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


if __name__ == "__main__":
    youtube_url = "https://www.youtube.com/watch?v=YFZBkHqGeFY"  # Example URL
    try:
        filename, title = download_audio_from_youtube(youtube_url)
        print(f"Downloaded audio: {filename} with title: {title}")
    except Exception as e:
        print(f"An error occurred: {e}")