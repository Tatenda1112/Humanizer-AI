from fastapi import APIRouter, Depends, HTTPException
from datetime import date
from middleware.auth import get_current_user
from services.supabase import get_supabase
from services import local_dev
from services import postgres

router = APIRouter()

PLAN_LIMITS = {
    "free":    {"daily": 300,   "monthly": None},
    "basic":   {"daily": None,  "monthly": 10_000},
    "premium": {"daily": None,  "monthly": None},
}


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    if postgres.enabled():
        return postgres.profile(current_user.id)
    if local_dev.enabled():
        return local_dev.profile()
    supabase = get_supabase()

    profile_res = (
        supabase.table("profiles").select("*").eq("id", current_user.id).single().execute()
    )
    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = profile_res.data
    plan = profile.get("plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    used_today = profile.get("words_used_today", 0)
    used_month = profile.get("words_used_month", 0)

    remaining_today = (
        max(0, limits["daily"] - used_today) if limits["daily"] is not None else None
    )
    remaining_month = (
        max(0, limits["monthly"] - used_month) if limits["monthly"] is not None else None
    )

    try:
        sub_res = (
            supabase.table("subscriptions")
            .select("current_period_end")
            .eq("user_id", current_user.id)
            .eq("status", "active")
            .maybe_single()
            .execute()
        )
        sub_end = sub_res.data.get("current_period_end") if sub_res and sub_res.data else None
    except Exception:
        sub_end = None

    return {
        "id": current_user.id,
        "email": profile.get("email"),
        "plan": plan,
        "preferred_provider": profile.get("preferred_provider", "claude"),
        "words_used_today": used_today,
        "words_used_month": used_month,
        "daily_limit": limits["daily"],
        "monthly_limit": limits["monthly"],
        "words_remaining_today": remaining_today,
        "words_remaining_month": remaining_month,
        "subscription_end_date": sub_end,
    }


@router.get("/history")
def get_history(current_user=Depends(get_current_user)):
    if postgres.enabled():
        return postgres.history(current_user.id)
    if local_dev.enabled():
        return local_dev.history()
    supabase = get_supabase()

    res = (
        supabase.table("humanizations")
        .select(
            "id, original_text, humanized_text, word_count, level, tone, "
            "ai_score_before, ai_score_after, provider, created_at"
        )
        .eq("user_id", current_user.id)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )

    return [
        {
            **row,
            "original_preview": (row["original_text"][:50] + "...")
            if len(row["original_text"]) > 50
            else row["original_text"],
            "humanized_preview": (row["humanized_text"][:50] + "...")
            if row.get("humanized_text") and len(row["humanized_text"]) > 50
            else row.get("humanized_text", ""),
        }
        for row in res.data
    ]


@router.post("/reset-daily")
def reset_daily(current_user=Depends(get_current_user)):
    if postgres.enabled():
        postgres.reset(current_user.id)
        return {'message': 'Usage reset'}
    if local_dev.enabled():
        local_dev.reset()
        return {"message": "Local usage reset"}
    supabase = get_supabase()
    today = str(date.today())

    supabase.table("profiles").update({
        "words_used_today": 0,
        "last_reset_date": today,
    }).lt("last_reset_date", today).execute()

    return {"message": "Daily limits reset successfully"}
