import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from routers import humanize, detect, user, stripe_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    provider = os.getenv("AI_PROVIDER", "claude").lower()
    print(f"[startup] AI_PROVIDER={provider}")

    if provider in ("claude", "both"):
        try:
            import anthropic
            anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            print("[startup] Anthropic client initialised OK")
        except Exception as exc:
            print(f"[startup] Anthropic warning: {exc}")

    if provider in ("openai", "both"):
        try:
            from openai import OpenAI
            OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            print("[startup] OpenAI client initialised OK")
        except Exception as exc:
            print(f"[startup] OpenAI warning: {exc}")

    yield


app = FastAPI(title="HumanizeAI API", version="1.0.0", lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "https://localhost:3000",
    os.getenv("FRONTEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in origins if o],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(humanize.router, prefix="/humanize", tags=["humanize"])
app.include_router(detect.router,   prefix="/detect",   tags=["detect"])
app.include_router(user.router,     prefix="/user",     tags=["user"])
app.include_router(stripe_router.router, prefix="/stripe", tags=["stripe"])


@app.get("/health")
async def health():
    return {"status": "ok", "provider": os.getenv("AI_PROVIDER", "claude")}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[error] {request.method} {request.url} — {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
