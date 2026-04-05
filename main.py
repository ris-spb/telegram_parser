from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    CHANNELS,
    DEBUG_COLUMNS,
    DEBUG_DIR,
    DEFAULT_DAYS,
    JSON_INDENT,
    MSK_TZ,
    OUTPUT_COLUMNS,
    OUTPUT_DIR,
)
from parser import run_parser


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Telegram parser: JSON / Excel export for public channels"
    )
    parser.add_argument(
        "--format",
        choices=["json", "xlsx", "both"],
        default="json",
        help="Формат сохранения результата",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help="Количество календарных дней",
    )
    parser.add_argument(
        "--include-today",
        action="store_true",
        help="Включать сегодняшний день в период",
    )
    parser.add_argument(
        "--save-debug",
        action="store_true",
        help="Сохранять debug-результат",
    )
    parser.add_argument(
        "--stdout-json",
        action="store_true",
        help="Печатать основной JSON с метаданными в консоль",
    )
    parser.add_argument(
        "--stdout-items-only",
        action="store_true",
        help="Печатать в консоль только массив items",
    )
    return parser.parse_args()


def build_period_dates(days: int, exclude_today: bool) -> tuple[date, date]:
    now_msk = datetime.now(MSK_TZ)
    today = now_msk.date()

    if exclude_today:
        period_start = today - timedelta(days=days)
        period_end = today - timedelta(days=1)
    else:
        period_start = today - timedelta(days=days - 1)
        period_end = today

    return period_start, period_end


def build_output_paths(days: int, exclude_today: bool) -> dict[str, Path]:
    period_start, period_end = build_period_dates(days=days, exclude_today=exclude_today)
    date_range = f"{period_start.strftime('%Y-%m-%d')}_{period_end.strftime('%Y-%m-%d')}"

    return {
        "json": OUTPUT_DIR / f"telegram_posts_{date_range}.json",
        "items_json": OUTPUT_DIR / f"telegram_posts_items_{date_range}.json",
        "xlsx": OUTPUT_DIR / f"telegram_posts_{date_range}.xlsx",
        "debug_json": DEBUG_DIR / f"telegram_posts_debug_{date_range}.json",
        "debug_xlsx": DEBUG_DIR / f"telegram_posts_debug_{date_range}.xlsx",
    }


def build_main_payload(
    items: list[dict[str, Any]],
    errors: list[dict[str, str]],
    days: int,
    exclude_today: bool,
) -> dict[str, Any]:
    period_start, period_end = build_period_dates(days=days, exclude_today=exclude_today)

    return {
        "generated_at": datetime.now(MSK_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Europe/Moscow",
        "days": days,
        "exclude_today": exclude_today,
        "period_start": str(period_start),
        "period_end": str(period_end),
        "channels": CHANNELS,
        "news_count": len(items),
        "errors_count": len(errors),
        "errors": errors,
        "items": items,
    }


def build_debug_payload(
    debug_items: list[dict[str, Any]],
    errors: list[dict[str, str]],
    days: int,
    exclude_today: bool,
) -> dict[str, Any]:
    period_start, period_end = build_period_dates(days=days, exclude_today=exclude_today)

    return {
        "generated_at": datetime.now(MSK_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Europe/Moscow",
        "days": days,
        "exclude_today": exclude_today,
        "period_start": str(period_start),
        "period_end": str(period_end),
        "debug_count": len(debug_items),
        "errors_count": len(errors),
        "errors": errors,
        "items": debug_items,
    }


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=JSON_INDENT)


def save_main_xlsx(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "Название канала": item["channel_name"],
            "Дата публикации": item["published_at"],
            "Текст публикации": item["text"],
        }
        for item in items
    ]

    df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    df.to_excel(path, index=False)


def save_debug_xlsx(path: Path, debug_items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(debug_items, columns=DEBUG_COLUMNS)
    df.to_excel(path, index=False)


async def main() -> None:
    args = parse_args()

    days = args.days
    exclude_today = not args.include_today

    if days <= 0:
        raise ValueError("--days должен быть больше 0")

    items, debug_items, errors = await run_parser(
        days=days,
        exclude_today=exclude_today,
    )

    paths = build_output_paths(days=days, exclude_today=exclude_today)

    main_payload = build_main_payload(
        items=items,
        errors=errors,
        days=days,
        exclude_today=exclude_today,
    )

    debug_payload = build_debug_payload(
        debug_items=debug_items,
        errors=errors,
        days=days,
        exclude_today=exclude_today,
    )

    if args.format in {"json", "both"}:
        save_json(paths["json"], main_payload)
        save_json(paths["items_json"], items)
        print(f"JSON с метаданными сохранен: {paths['json']}")
        print(f"Flat JSON-массив сохранен: {paths['items_json']}")

    if args.format in {"xlsx", "both"}:
        save_main_xlsx(paths["xlsx"], items)
        print(f"Excel сохранен: {paths['xlsx']}")

    if args.save_debug:
        if args.format in {"json", "both"}:
            save_json(paths["debug_json"], debug_payload)
            print(f"Debug JSON сохранен: {paths['debug_json']}")

        if args.format in {"xlsx", "both"}:
            save_debug_xlsx(paths["debug_xlsx"], debug_items)
            print(f"Debug Excel сохранен: {paths['debug_xlsx']}")

    print(f"Собрано новостей: {len(items)}")
    print(f"Debug-строк: {len(debug_items)}")
    print(f"Ошибок по каналам: {len(errors)}")

    if args.stdout_items_only:
        print(json.dumps(items, ensure_ascii=False, indent=JSON_INDENT))
    elif args.stdout_json:
        print(json.dumps(main_payload, ensure_ascii=False, indent=JSON_INDENT))


if __name__ == "__main__":
    asyncio.run(main())