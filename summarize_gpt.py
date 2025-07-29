import openai
import os
import textwrap
import dotenv
dotenv.load_dotenv()  # Load environment variables from .env file
MAX_CHARS_PER_CHUNK = 4000  # מוערך כ־1000 טוקנים
MODEL = "gpt-4"

def summarize_chunk(chunk, client):
    messages = [
        {
            "role": "system",
            "content": "Summarize the following part of a podcast transcript into 2-3 concise bullet points in Hebrew."
        },
        {
            "role": "user",
            "content": chunk
        }
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def summarize_text(full_text: str) -> str:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # חלק את הטקסט לחתיכות בגודל מתאים
    chunks = textwrap.wrap(full_text, MAX_CHARS_PER_CHUNK)

    partial_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"🧩 Summarizing chunk {i+1}/{len(chunks)}...")
        summary = summarize_chunk(chunk, client)
        partial_summaries.append(summary)

    # עכשיו נסכם את הסיכומים (אם צריך)
    combined = "\n".join(partial_summaries)
    print("📚 Final summary synthesis...")

    final_summary = summarize_chunk(combined, client)
    return final_summary

if __name__ == "__main__":
    text = open(r"C:\not_work\daily_karnaf\downloads\YFZBkHqGeFY_transcript.txt", "r", encoding="utf-8").read() 
    
    try:
        summary = summarize_text(text)
        print(f"Final Summary:\n{summary}")
    except Exception as e:
        print(f"Error occurred while summarizing: {e}")