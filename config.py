from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
DEBUG_DIR = BASE_DIR / "debug"
SESSIONS_DIR = BASE_DIR / "sessions"

SESSION_NAME = SESSIONS_DIR / "telegram_parser_session"

# Заполните своими данными
API_ID = 28346057
API_HASH = "eeb94bc07e8fbe3fe769c4d4b97c4b77"
PHONE = "+79312058438"

CHANNELS = [
    "tourdom",
    "premni",
    "ranarod",
    "intouristpro",
    "fsexpert_media",
    "aeroflot_pr",
    "avia_news_ru",
    "Avianity",
    "aviaru_news",
    "maya_kotlyar",
    "Rossiya_airlines_official",
    "PobedaAirlines",
]

MSK_TZ = ZoneInfo("Europe/Moscow")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_ONLY_FORMAT = "%Y-%m-%d"
TIME_ONLY_FORMAT = "%H:%M:%S"

DEFAULT_DAYS = 7
DEFAULT_EXCLUDE_TODAY = True

JSON_INDENT = 2
TEXT_PREVIEW_LENGTH = 220
SOFT_SIGNATURE_WORDS = 30

OUTPUT_COLUMNS = [
    "Название канала",
    "Дата публикации",
    "Текст публикации",
]

DEBUG_COLUMNS = [
    "channel_username",
    "channel_title",
    "message_id",
    "grouped_id",
    "date_utc",
    "date_msk",
    "post_type",
    "has_media",
    "raw_text",
    "normalized_text",
    "text_length",
    "dedupe_exact_key",
    "dedupe_soft_key",
    "source_url",
]