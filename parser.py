from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from typing import Any

from telethon import TelegramClient

from config import (
    API_HASH,
    API_ID,
    CHANNELS,
    DATE_FORMAT,
    DATE_ONLY_FORMAT,
    MSK_TZ,
    PHONE,
    SESSION_NAME,
    SOFT_SIGNATURE_WORDS,
    TEXT_PREVIEW_LENGTH,
    TIME_ONLY_FORMAT,
)

URL_RE = re.compile(r"(https?://\S+|www\.\S+|t\.me/\S+)", flags=re.IGNORECASE)
MENTION_RE = re.compile(r"@\w+", flags=re.IGNORECASE)
NON_WORD_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
WHITESPACE_RE = re.compile(r"\s+", flags=re.UNICODE)


def get_date_range_msk(days: int, exclude_today: bool = True) -> tuple[datetime, datetime]:
    now_msk = datetime.now(MSK_TZ)
    today = now_msk.date()

    if exclude_today:
        end_date = today
        start_date = today - timedelta(days=days)
    else:
        end_date = today + timedelta(days=1)
        start_date = today - timedelta(days=days - 1)

    start_msk = datetime.combine(start_date, time.min, tzinfo=MSK_TZ)
    end_msk = datetime.combine(end_date, time.min, tzinfo=MSK_TZ)

    return start_msk, end_msk


def to_msk(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MSK_TZ)


def clean_text(text: str | None) -> str:
    if text is None:
        return ""

    cleaned = str(text)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("\xa0", " ")
    cleaned = cleaned.strip()

    return cleaned


def make_preview(text: str, limit: int = TEXT_PREVIEW_LENGTH) -> str:
    if not text:
        return ""

    one_line = WHITESPACE_RE.sub(" ", text).strip()
    if len(one_line) <= limit:
        return one_line

    return one_line[:limit].rstrip() + "..."


def normalize_for_dedupe(text: str) -> str:
    if not text:
        return ""

    normalized = text.lower().replace("ё", "е")
    normalized = URL_RE.sub(" ", normalized)
    normalized = MENTION_RE.sub(" ", normalized)
    normalized = NON_WORD_RE.sub(" ", normalized)
    normalized = normalized.replace("_", " ")
    normalized = WHITESPACE_RE.sub(" ", normalized).strip()

    return normalized


def build_soft_signature(normalized_text: str, words_limit: int = SOFT_SIGNATURE_WORDS) -> str:
    if not normalized_text:
        return ""

    words = normalized_text.split()
    return " ".join(words[:words_limit])


def hash_value(value: str) -> str:
    if not value:
        return ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_message_text(message: Any) -> str:
    text_candidates = [
        getattr(message, "message", None),
        getattr(message, "text", None),
        getattr(message, "raw_text", None),
    ]

    for text in text_candidates:
        if text is not None:
            return clean_text(text)

    return ""


def get_post_type(message: Any) -> str:
    if getattr(message, "grouped_id", None):
        return "media_group_item"
    if getattr(message, "media", None):
        return "media_post"
    return "text_post"


def build_source_url(channel_username: str, message_id: int | None) -> str:
    if not channel_username or message_id is None:
        return ""
    return f"https://t.me/{channel_username}/{message_id}"


def build_item_id(channel_username: str, message_id: int | None, grouped_id: int | None) -> str:
    if grouped_id is not None:
        return f"{channel_username}_group_{grouped_id}"
    if message_id is not None:
        return f"{channel_username}_{message_id}"
    return f"{channel_username}_unknown"


def build_briefing_input(
    channel_name: str,
    channel_username: str,
    published_at: str,
    source_url: str,
    text: str,
) -> str:
    safe_text = text if text else "[без текста]"
    return (
        f"Источник: Telegram / {channel_name} (@{channel_username})\n"
        f"Дата: {published_at}\n"
        f"Ссылка: {source_url}\n"
        f"Текст: {safe_text}"
    )


def build_news_item(
    *,
    channel_name: str,
    channel_username: str,
    date_msk_dt: datetime,
    date_utc_dt: datetime | None,
    text: str,
    message_id: int | None,
    grouped_id: int | None,
    post_type: str,
    has_media: bool,
    source_url: str,
    album_message_ids: list[int] | None = None,
) -> dict[str, Any]:
    cleaned_text = clean_text(text)
    normalized_text = normalize_for_dedupe(cleaned_text)
    soft_signature = build_soft_signature(normalized_text)

    published_at = date_msk_dt.strftime(DATE_FORMAT)
    published_date = date_msk_dt.strftime(DATE_ONLY_FORMAT)
    published_time = date_msk_dt.strftime(TIME_ONLY_FORMAT)
    published_at_utc = date_utc_dt.strftime(DATE_FORMAT) if date_utc_dt else ""

    item = {
        "item_id": build_item_id(channel_username, message_id, grouped_id),
        "source_type": "telegram_channel",
        "channel_name": channel_name,
        "channel_username": channel_username,
        "published_at": published_at,
        "published_at_iso": date_msk_dt.isoformat(),
        "published_at_unix": int(date_msk_dt.timestamp()),
        "published_at_utc": published_at_utc,
        "published_date": published_date,
        "published_time": published_time,
        "text": cleaned_text,
        "text_preview": make_preview(cleaned_text),
        "normalized_text": normalized_text,
        "soft_signature": soft_signature,
        "dedupe_exact_key": hash_value(normalized_text),
        "dedupe_soft_key": hash_value(soft_signature),
        "message_id": message_id,
        "grouped_id": grouped_id,
        "album_message_ids": album_message_ids or ([] if message_id is None else [message_id]),
        "post_type": post_type,
        "has_media": has_media,
        "has_text": bool(cleaned_text),
        "text_length": len(cleaned_text),
        "normalized_text_length": len(normalized_text),
        "source_url": source_url,
        "category_main": "",
        "category_sub": "",
        "priority": "",
        "briefing_input": build_briefing_input(
            channel_name=channel_name,
            channel_username=channel_username,
            published_at=published_at,
            source_url=source_url,
            text=cleaned_text,
        ),
        "_published_at_dt": date_msk_dt,
    }

    return item


async def collect_channel_messages(
    client: TelegramClient,
    days: int,
    exclude_today: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    start_msk, end_msk = get_date_range_msk(days=days, exclude_today=exclude_today)

    output_rows: list[dict[str, Any]] = []
    debug_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for channel_username in CHANNELS:
        try:
            entity = await client.get_entity(channel_username)
            channel_title = getattr(entity, "title", channel_username)
        except Exception as exc:
            errors.append(
                {
                    "channel_username": channel_username,
                    "stage": "get_entity",
                    "error": str(exc),
                }
            )
            continue

        grouped_posts: dict[int, list[dict[str, Any]]] = defaultdict(list)
        single_posts: list[dict[str, Any]] = []

        try:
            async for message in client.iter_messages(entity):
                if message is None or getattr(message, "date", None) is None:
                    continue

                date_utc = message.date
                date_msk = to_msk(date_utc)

                if date_msk < start_msk:
                    break

                if not (start_msk <= date_msk < end_msk):
                    continue

                message_id = getattr(message, "id", None)
                grouped_id = getattr(message, "grouped_id", None)
                has_media = getattr(message, "media", None) is not None
                post_type = get_post_type(message)
                raw_text = get_message_text(message)
                source_url = build_source_url(channel_username, message_id)

                raw_item = build_news_item(
                    channel_name=channel_title,
                    channel_username=channel_username,
                    date_msk_dt=date_msk,
                    date_utc_dt=date_utc,
                    text=raw_text,
                    message_id=message_id,
                    grouped_id=grouped_id,
                    post_type=post_type,
                    has_media=has_media,
                    source_url=source_url,
                )

                debug_rows.append(
                    {
                        "channel_username": channel_username,
                        "channel_title": channel_title,
                        "message_id": message_id,
                        "grouped_id": grouped_id,
                        "date_utc": raw_item["published_at_utc"],
                        "date_msk": raw_item["published_at"],
                        "post_type": post_type,
                        "has_media": has_media,
                        "raw_text": raw_item["text"],
                        "normalized_text": raw_item["normalized_text"],
                        "text_length": raw_item["text_length"],
                        "dedupe_exact_key": raw_item["dedupe_exact_key"],
                        "dedupe_soft_key": raw_item["dedupe_soft_key"],
                        "source_url": raw_item["source_url"],
                    }
                )

                if grouped_id:
                    grouped_posts[grouped_id].append(raw_item)
                else:
                    single_posts.append(raw_item)

        except Exception as exc:
            errors.append(
                {
                    "channel_username": channel_username,
                    "stage": "iter_messages",
                    "error": str(exc),
                }
            )
            continue

        for grouped_id, items in grouped_posts.items():
            items_sorted = sorted(
                items,
                key=lambda x: (x["_published_at_dt"], x["message_id"] or 0),
            )

            combined_text = ""
            for item in items_sorted:
                if item["text"]:
                    combined_text = item["text"]
                    break

            first_item = items_sorted[0]
            album_message_ids = [
                item["message_id"] for item in items_sorted if item["message_id"] is not None
            ]

            grouped_item = build_news_item(
                channel_name=first_item["channel_name"],
                channel_username=first_item["channel_username"],
                date_msk_dt=first_item["_published_at_dt"],
                date_utc_dt=datetime.fromisoformat(first_item["published_at_iso"]).astimezone(timezone.utc),
                text=combined_text,
                message_id=first_item["message_id"],
                grouped_id=grouped_id,
                post_type="media_group",
                has_media=True,
                source_url=first_item["source_url"],
                album_message_ids=album_message_ids,
            )

            output_rows.append(grouped_item)

        for item in single_posts:
            output_rows.append(item)

    output_rows = sorted(
        output_rows,
        key=lambda x: (
            x["_published_at_dt"],
            x["channel_username"],
            x["message_id"] or 0,
        ),
    )

    for row in output_rows:
        row.pop("_published_at_dt", None)

    debug_rows = sorted(
        debug_rows,
        key=lambda x: (
            x["date_msk"],
            x["channel_username"],
            str(x["message_id"]),
        ),
    )

    return output_rows, debug_rows, errors


async def run_parser(
    days: int,
    exclude_today: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    if not API_ID or not API_HASH or not PHONE:
        raise ValueError("Заполните API_ID, API_HASH и PHONE в config.py")

    client = TelegramClient(str(SESSION_NAME), API_ID, API_HASH)

    await client.start(phone=PHONE)
    try:
        output_rows, debug_rows, errors = await collect_channel_messages(
            client=client,
            days=days,
            exclude_today=exclude_today,
        )
    finally:
        await client.disconnect()

    return output_rows, debug_rows, errors