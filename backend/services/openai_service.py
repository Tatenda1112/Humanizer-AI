import os
import time
from openai import OpenAI, RateLimitError, APIStatusError
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert human writing editor.
Rewrite AI-generated text to sound naturally human-written.
NEVER change: numbers, statistics, percentages, proper nouns,
names, places, companies, technical terms, or facts.
ALWAYS: replace AI transition words (furthermore, moreover,
in conclusion, it is important to note, this demonstrates,
notably, additionally), add contractions (it's, don't, can't),
vary sentence length, mix short punchy sentences with longer
flowing ones.
LEVEL: light=subtle changes, medium=moderate,
aggressive=complete rephrase
TONE: academic/casual/professional/friendly/creative
OUTPUT: rewritten text only. No explanations. No preamble."""


def call_openai_humanizer(text: str, level: str, tone: str, is_paid_user: bool) -> dict:
    model = (
        os.getenv("OPENAI_MODEL_PAID", "gpt-4o")
        if is_paid_user
        else os.getenv("OPENAI_MODEL_FREE", "gpt-4o-mini")
    )

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=4096,
                temperature=0.9,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"LEVEL: {level}\nTONE: {tone}\n\nTEXT:\n{text}"}
                ]
            )
            return {
                "humanized_text": response.choices[0].message.content,
                "model_used": model,
            }
        except RateLimitError:
            if attempt == 0:
                time.sleep(2)
                continue
            raise
        except APIStatusError as exc:
            if exc.status_code in (500, 503) and attempt == 0:
                time.sleep(2)
                continue
            raise

    raise RuntimeError("OpenAI humanizer failed after retry")
