from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
SESSIONS_DIR = BASE_DIR / "sessions"

SESSION_NAME = SESSIONS_DIR / "telegram_parser_session"

# Telegram API credentials
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
TEXT_PREVIEW_LENGTH = 220
SOFT_SIGNATURE_WORDS = 30

OUTPUT_COLUMNS = [
    "Название канала",
    "Дата публикации",
    "Текст публикации",
    "Ссылка на публикацию",
]
