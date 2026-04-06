from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from config import DEFAULT_DAYS
from excel_export import build_metadata, build_output_path, save_excel
from parser import run_parser


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Telegram parser: выгрузка публикаций в Excel"
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
        "--output",
        type=str,
        default="",
        help="Полный путь до Excel-файла. Если не указан, файл будет сохранен в папку output",
    )
    parser.add_argument(
        "--print-meta",
        action="store_true",
        help="Печатать в консоль краткую метаинформацию по выгрузке",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if args.days <= 0:
        raise ValueError("--days должен быть больше 0")

    exclude_today = not args.include_today
    items, errors = await run_parser(days=args.days, exclude_today=exclude_today)

    output_path = Path(args.output) if args.output else build_output_path(
        days=args.days,
        exclude_today=exclude_today,
    )
    saved_path = save_excel(output_path, items)

    print(f"Excel сохранен: {saved_path}")
    print(f"Собрано новостей: {len(items)}")
    print(f"Ошибок по каналам: {len(errors)}")

    if args.print_meta:
        meta = build_metadata(
            items=items,
            errors=errors,
            days=args.days,
            exclude_today=exclude_today,
        )
        print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
