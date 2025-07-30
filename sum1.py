import os
import ast
import tiktoken
from openai import OpenAI
import dotenv
dotenv.load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

MODEL = "gpt-4o"
MAX_CONTEXT = 128_000
MAX_OUTPUT = 4000

# Prompt tailored for your use-case
PROMPT_INSTRUCTIONS = (
    "You are a professional summarizer. You will receive a transcript of a daily news podcast in Hebrew.\n"
    "Your task:\n"
    "- Summarize the entire content into 2–4 short Hebrew tweets.\n"
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

    # Save as a text file
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(repr(summary))

    print("Summary list:", summary)
    return summary

if __name__ == "__main__":
    import sys
    from utils import post_tweets1
    path = r"downloads\YFZBkHqGeFY_transcript.txt"
    tweets = summarize_transcript_file(path)
    post_tweets1(tweets)
