"""Explicit, opt-in local mode. All data disappears when the process restarts."""
import os
from threading import Lock
from datetime import datetime, timezone
from uuid import uuid4


def enabled() -> bool:
    return os.getenv('LOCAL_DEV_MODE', '').lower() == 'true'


USER_ID = '00000000-0000-4000-8000-000000000001'
_lock = Lock()
_words = 0
_history: list[dict] = []


def profile() -> dict:
    with _lock:
        return dict(id=USER_ID, email='developer@localhost', plan='premium',
                    preferred_provider='claude', words_used_today=_words,
                    words_used_month=_words, daily_limit=None, monthly_limit=None,
                    words_remaining_today=None, words_remaining_month=None,
                    subscription_end_date=None)


def record(text: str, result: dict, level: str, tone: str) -> None:
    global _words
    with _lock:
        _words += len(text.split())
        _history.insert(0, dict(id=str(uuid4()), original_text=text,
            humanized_text=result['humanized_text'], original_preview=text[:50],
            humanized_preview=result['humanized_text'][:50], word_count=len(text.split()),
            level=level, tone=tone, provider=result['provider'],
            ai_score_before=None, ai_score_after=None,
            created_at=datetime.now(timezone.utc).isoformat()))
        del _history[20:]


def history() -> list[dict]:
    with _lock:
        return [dict(row) for row in _history]


def reset() -> None:
    global _words
    with _lock:
        _words = 0
