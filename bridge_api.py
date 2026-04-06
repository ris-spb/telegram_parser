from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from config import CHANNELS, DEFAULT_DAYS, MSK_TZ
from excel_export import build_metadata, build_output_path, save_excel
from parser import run_parser

app = FastAPI(title="Telegram Parser Bridge", version="2.0.0")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "telegram_parser_bridge",
        "time_msk": datetime.now(MSK_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "channels_count": len(CHANNELS),
        "output_format": "xlsx",
    }


@app.get("/parse/meta")
async def parse_meta(
    days: int = Query(default=DEFAULT_DAYS, ge=1, le=30),
    include_today: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        items, errors = await run_parser(
            days=days,
            exclude_today=not include_today,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return build_metadata(
        items=items,
        errors=errors,
        days=days,
        exclude_today=not include_today,
    )


@app.post("/parse")
@app.get("/parse")
async def parse_news(
    days: int = Query(default=DEFAULT_DAYS, ge=1, le=30),
    include_today: bool = Query(default=False),
) -> FileResponse:
    try:
        items, errors = await run_parser(
            days=days,
            exclude_today=not include_today,
        )
        output_path = build_output_path(days=days, exclude_today=not include_today)
        saved_path = save_excel(output_path, items)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not Path(saved_path).exists():
        raise HTTPException(status_code=500, detail="Excel файл не был создан")

    return FileResponse(
        path=str(saved_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=Path(saved_path).name,
        headers={
            "X-News-Count": str(len(items)),
            "X-Errors-Count": str(len(errors)),
        },
    )
