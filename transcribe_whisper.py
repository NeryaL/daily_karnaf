import openai
import dotenv
import os



def transcribe_audio(mp3_path: str) -> str:
    dotenv.load_dotenv()  # Load environment variables from .env file
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print(f"🔁 Transcribing: {mp3_path}")
    
    with open(mp3_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    return transcript


if __name__ == "__main__":
    
    mp3_path = r"downloads\My_Podcast_Episode.mp3"  # Replace with your actual file path
    try:
        transcription = transcribe_audio(mp3_path)
        print(f"Transcription:\n{transcription}")
    except Exception as e:
        print(f"An error occurred during transcription: {e}")