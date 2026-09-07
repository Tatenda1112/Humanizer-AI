from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import date
from middleware.auth import get_current_user
from services.ai_provider import call_humanizer
from services.supabase import get_supabase

router = APIRouter()

PLAN_LIMITS = {
    "free":    {"daily": 300,   "monthly": None},
    "basic":   {"daily": None,  "monthly": 10_000},
    "premium": {"daily": None,  "monthly": None},
}


class HumanizeRequest(BaseModel):
    text: str
    level: str = "medium"
    tone: str = "professional"
    mode: str = "ghost_2"


@router.post("")
async def humanize_text(req: HumanizeRequest, current_user=Depends(get_current_user)):
    supabase = get_supabase()

    profile_res = (
        supabase.table("profiles").select("*").eq("id", current_user.id).single().execute()
    )
    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = profile_res.data
    plan = profile.get("plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    word_count = len(req.text.split())

    # Enforce mode access by plan:
    # free plan → always Ghost 1 (DeepSeek), Ghost 2 is paid only
    mode = req.mode
    if plan == "free":
        mode = "ghost_1"

    # DEV MODE: limits disabled during development
    if False and limits["daily"] is not None:
        used = profile.get("words_used_today", 0)
        if used + word_count > limits["daily"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Daily word limit exceeded",
                    "plan": plan,
                    "limit": limits["daily"],
                    "used": used,
                },
            )

    if False and limits["monthly"] is not None:
        used = profile.get("words_used_month", 0)
        if used + word_count > limits["monthly"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Monthly word limit exceeded",
                    "plan": plan,
                    "limit": limits["monthly"],
                    "used": used,
                },
            )

    is_paid = plan in ("basic", "premium")
    result = call_humanizer(req.text, req.level, req.tone, is_paid, mode=mode)

    supabase.table("humanizations").insert({
        "user_id": current_user.id,
        "original_text": req.text,
        "humanized_text": result["humanized_text"],
        "provider": result["provider"],
        "model_used": result["model_used"],
        "word_count": word_count,
        "level": req.level,
        "tone": req.tone,
    }).execute()

    new_daily = profile.get("words_used_today", 0) + word_count
    new_monthly = profile.get("words_used_month", 0) + word_count
    supabase.table("profiles").update({
        "words_used_today": new_daily,
        "words_used_month": new_monthly,
        "last_reset_date": str(date.today()),
    }).eq("id", current_user.id).execute()

    words_remaining: int | None = None
    if limits["daily"] is not None:
        words_remaining = max(0, limits["daily"] - new_daily)
    elif limits["monthly"] is not None:
        words_remaining = max(0, limits["monthly"] - new_monthly)

    return {
        "humanized_text": result["humanized_text"],
        "words_used": word_count,
        "words_remaining": words_remaining,
        "mode_name": result["mode_name"],
        "provider": result["provider"],
    }
