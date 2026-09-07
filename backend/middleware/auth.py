from fastapi import Header, HTTPException, Request
from services.supabase import get_supabase
from services import local_dev
from services import postgres
from types import SimpleNamespace


def get_current_user(request: Request, authorization: str | None = Header(default=None)):
    if postgres.enabled():
        user = postgres.authenticate(request.cookies.get(postgres.COOKIE))
        if not user:
            raise HTTPException(status_code=401, detail='Please sign in')
        return user
    if local_dev.enabled():
        return SimpleNamespace(id=local_dev.USER_ID, email='developer@localhost')
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.split(" ", 1)[1]
    supabase = get_supabase()

    try:
        res = supabase.auth.get_user(token)
        if not res.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return res.user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
