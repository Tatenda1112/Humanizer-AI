import os
from openai import OpenAI, APIError
from services.rewrite import Completion, ProviderUnavailableError, SYSTEM_PROMPT, clean_output, rewrite


def call_deepseek_humanizer(text: str, level: str, tone: str, is_paid_user: bool) -> dict:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ProviderUnavailableError("Ghost 1 is not configured.")
    model = os.getenv("DEEPSEEK_MODEL_PAID" if is_paid_user else "DEEPSEEK_MODEL_FREE",
                      "deepseek-v4-pro" if is_paid_user else "deepseek-v4-flash")
    try:
        with OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=60.0, max_retries=1) as client:
            def generate(prompt: str, max_tokens: int) -> Completion:
                response = client.chat.completions.create(
                    model=model, max_tokens=max_tokens, temperature=0.7,
                    extra_body={"thinking": {"type": "disabled"}},
                    messages=[{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": prompt}],
                )
                choice = response.choices[0]
                return Completion(
                    text=choice.message.content or "", complete=choice.finish_reason == "stop",
                    input_tokens=response.usage.prompt_tokens if response.usage else 0,
                    output_tokens=response.usage.completion_tokens if response.usage else 0,
                )
            result = rewrite(text, level, tone, generate, review=True,
                             planning=os.getenv('REWRITE_USE_PLAN', 'false').lower() == 'true')
    except APIError as exc:
        raise ProviderUnavailableError("Ghost 1 is temporarily unavailable. Please try again.") from exc
    return {**result, "model_used": model}
