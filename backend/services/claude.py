import os
import anthropic
from services.rewrite import Completion, ProviderUnavailableError, SYSTEM_PROMPT, clean_output, rewrite


def call_claude_humanizer(text: str, level: str, tone: str, is_paid_user: bool) -> dict:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ProviderUnavailableError("Ghost 2 is not configured.")
    model = os.getenv("ANTHROPIC_MODEL_PAID" if is_paid_user else "ANTHROPIC_MODEL_FREE", "claude-sonnet-4-6")
    try:
        with anthropic.Anthropic(api_key=key, timeout=60.0, max_retries=1) as client:
            def generate(prompt: str, max_tokens: int) -> Completion:
                response = client.messages.create(
                    model=model, max_tokens=max_tokens,
                    system=SYSTEM_PROMPT, messages=[{"role": "user", "content": prompt}],
                )
                return Completion(
                    text="".join(block.text for block in response.content if block.type == "text"),
                    complete=response.stop_reason == "end_turn",
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
            result = rewrite(text, level, tone, generate, review=True,
                             planning=os.getenv('REWRITE_USE_PLAN', 'false').lower() == 'true')
    except anthropic.APIError as exc:
        raise ProviderUnavailableError("Ghost 2 is temporarily unavailable. Please try again.") from exc
    return {**result, "model_used": model}
