import os
import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from middleware.auth import get_current_user
from services.supabase import get_supabase

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICE_MAP = {
    "basic":   os.getenv("STRIPE_PRICE_BASIC", ""),
    "premium": os.getenv("STRIPE_PRICE_PREMIUM", ""),
}


class CheckoutRequest(BaseModel):
    plan: str


@router.post("/checkout")
async def create_checkout(req: CheckoutRequest, current_user=Depends(get_current_user)):
    price_id = PRICE_MAP.get(req.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {req.plan}")

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{frontend_url}/dashboard?success=true",
        cancel_url=f"{frontend_url}/pricing",
        metadata={"user_id": current_user.id, "plan": req.plan},
    )
    return {"url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    supabase = get_supabase()
    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = obj["metadata"]["user_id"]
        plan = obj["metadata"]["plan"]
        supabase.table("profiles").update({"plan": plan}).eq("id", user_id).execute()
        supabase.table("subscriptions").upsert({
            "user_id": user_id,
            "stripe_customer_id": obj["customer"],
            "stripe_subscription_id": obj["subscription"],
            "plan": plan,
            "status": "active",
        }).execute()

    elif event_type == "customer.subscription.deleted":
        res = (
            supabase.table("subscriptions")
            .select("user_id")
            .eq("stripe_subscription_id", obj["id"])
            .maybe_single()
            .execute()
        )
        if res.data:
            user_id = res.data["user_id"]
            supabase.table("profiles").update({"plan": "free"}).eq("id", user_id).execute()
            supabase.table("subscriptions").update({"status": "canceled"}).eq(
                "stripe_subscription_id", obj["id"]
            ).execute()

    elif event_type == "customer.subscription.updated":
        res = (
            supabase.table("subscriptions")
            .select("user_id")
            .eq("stripe_subscription_id", obj["id"])
            .maybe_single()
            .execute()
        )
        if res.data:
            user_id = res.data["user_id"]
            plan = obj.get("metadata", {}).get("plan", "basic")
            supabase.table("profiles").update({"plan": plan}).eq("id", user_id).execute()
            supabase.table("subscriptions").update({
                "status": obj["status"],
                "current_period_end": obj.get("current_period_end"),
            }).eq("stripe_subscription_id", obj["id"]).execute()

    return {"received": True}


@router.get("/portal")
async def billing_portal(current_user=Depends(get_current_user)):
    supabase = get_supabase()

    sub_res = (
        supabase.table("subscriptions")
        .select("stripe_customer_id")
        .eq("user_id", current_user.id)
        .maybe_single()
        .execute()
    )
    if not sub_res.data:
        raise HTTPException(status_code=404, detail="No subscription found")

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    portal = stripe.billing_portal.Session.create(
        customer=sub_res.data["stripe_customer_id"],
        return_url=f"{frontend_url}/dashboard",
    )
    return {"url": portal.url}
