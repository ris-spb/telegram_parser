from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from config import CHANNELS, MSK_TZ
from parser import run_parser

app = FastAPI(title="Telegram Parser Bridge", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "telegram_parser_bridge",
        "time_msk": datetime.now(MSK_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "channels_count": len(CHANNELS),
    }


@app.post("/parse")
@app.get("/parse")
async def parse_news(
    days: int = Query(default=7, ge=1, le=30),
    include_today: bool = Query(default=False),
    items_only: bool = Query(default=False),
) -> JSONResponse:
    try:
        items, debug_items, errors = await run_parser(
            days=days,
            exclude_today=not include_today,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    now_msk = datetime.now(MSK_TZ)
    today = now_msk.date()

    if include_today:
        period_start = today.fromordinal(today.toordinal() - (days - 1))
        period_end = today
    else:
        period_start = today.fromordinal(today.toordinal() - days)
        period_end = today.fromordinal(today.toordinal() - 1)

    if items_only:
        return JSONResponse(content=items)

    payload = {
        "generated_at": now_msk.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Europe/Moscow",
        "days": days,
        "exclude_today": not include_today,
        "period_start": str(period_start),
        "period_end": str(period_end),
        "channels": CHANNELS,
        "news_count": len(items),
        "debug_count": len(debug_items),
        "errors_count": len(errors),
        "errors": errors,
        "items": items,
    }

    return JSONResponse(content=payload)