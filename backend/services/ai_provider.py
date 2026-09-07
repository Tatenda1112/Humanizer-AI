import os
from dotenv import load_dotenv
from services.rewrite import ProviderUnavailableError

load_dotenv()


def call_humanizer(
    text: str,
    level: str,
    tone: str,
    is_paid_user: bool,
    mode: str = "ghost_2",
) -> dict:
    """
    mode options:
      ghost_2  — Claude Sonnet (premium, paid-tier quality)
      ghost_1  — DeepSeek (standard, free-tier quality)
      auto     — free users get Ghost 1, paid users get Ghost 2
    """

    resolved = mode

    if mode == "auto":
        resolved = "ghost_2" if is_paid_user else "ghost_1"

    # Keep free-tier costs and selected modes predictable; never silently upgrade.
    if resolved == "ghost_1" and not os.getenv("DEEPSEEK_API_KEY"):
        raise ProviderUnavailableError("Ghost 1 is not configured.")

    if resolved == "ghost_1":
        from services.deepseek_service import call_deepseek_humanizer
        result = call_deepseek_humanizer(text, level, tone, is_paid_user)
        result["mode_name"] = "Ghost 1"
        result["provider"] = "deepseek"
        return result

    if resolved == "ghost_2":
        from services.claude import call_claude_humanizer
        result = call_claude_humanizer(text, level, tone, is_paid_user)
        result["mode_name"] = "Ghost 2"
        result["provider"] = "claude"
        return result

    raise ValueError(
        f"Invalid mode '{mode}'. Must be 'ghost_1', 'ghost_2', or 'auto'."
    )
