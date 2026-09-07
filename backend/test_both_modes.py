"""
Run from backend/ with:
    python test_both_modes.py

Make sure ANTHROPIC_API_KEY and DEEPSEEK_API_KEY are set in .env
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from services.ai_provider import call_humanizer

TEST_TEXT = (
    "The rapid escalation of cyber threats in modern networked environments has "
    "exposed the limitations of traditional security mechanisms, which often fail "
    "to detect, interpret, and respond effectively to sophisticated and evolving "
    "attacks. This project proposes the development of an AI-Powered Network "
    "Intrusion Detection and Breach Analysis System that combines the power of "
    "machine learning (ML) and explainable artificial intelligence (XAI) to "
    "enhance cyber defense capabilities."
)

LEVEL = "aggressive"
TONE  = "academic"


def run(label: str, mode: str):
    print(f"\n{'=' * 50}")
    print(f"=== {label} ===")
    print("=" * 50)
    try:
        result = call_humanizer(
            text=TEST_TEXT,
            level=LEVEL,
            tone=TONE,
            is_paid_user=True,
            mode=mode,
        )
        print(result["humanized_text"])
        print(f"\n[model: {result['model_used']} | mode: {result['mode_name']}]")
    except Exception as exc:
        print(f"ERROR: {exc}")


if __name__ == "__main__":
    print(f"Test input ({len(TEST_TEXT.split())} words):")
    print(f"  {TEST_TEXT[:120]}...")
    print(f"\nLevel: {LEVEL}  |  Tone: {TONE}")

    run("GHOST 1 (DeepSeek)", mode="ghost_1")
    run("GHOST 2 (Claude)",   mode="ghost_2")

    print("\n" + "=" * 50)
    print("Done.")
