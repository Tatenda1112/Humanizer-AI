import os
import asyncio
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

ZEROGPT_URL = "https://api.zerogpt.com/api/detect/detectText"
MOCK_RESULT = {"ai_score": 50, "human_score": 50, "sentences": []}


async def _call_zerogpt(text: str) -> dict:
    api_key = os.getenv("ZEROGPT_API_KEY", "")
    if not api_key:
        return MOCK_RESULT
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                ZEROGPT_URL,
                headers={"ApiKey": api_key},
                json={"inputText": text},
            )
            data = resp.json()
            return {
                "ai_score": data.get("aiScore", 50),
                "human_score": data.get("humanScore", 50),
                "sentences": data.get("sentences", []),
            }
    except Exception:
        return MOCK_RESULT


class DetectRequest(BaseModel):
    text: str


class CompareRequest(BaseModel):
    original: str
    humanized: str


@router.post("")
async def detect_ai(req: DetectRequest):
    return await _call_zerogpt(req.text)


@router.post("/compare")
async def compare_scores(req: CompareRequest):
    before, after = await asyncio.gather(
        _call_zerogpt(req.original),
        _call_zerogpt(req.humanized),
    )
    return {
        "before": before,
        "after": after,
        "improvement": round(before["ai_score"] - after["ai_score"], 1),
    }
