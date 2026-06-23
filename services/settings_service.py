import json
import os
from dataclasses import dataclass, field


DEFAULT_LANGUAGE = "zh"
SUPPORTED_LANGUAGES = frozenset({"zh", "en"})
DEFAULT_TEMPLATE = "{name}_{start}-{end}.pdf"
DEFAULT_EPUB_PAPER = "a4"
DEFAULT_RECENT_LIMIT = 8


def _normalize_string(value, default: str = "") -> str:
    if not isinstance(value, str):
        return default

    normalized = value.strip()
    return normalized if normalized else default


def normalize_language(lang, default: str = DEFAULT_LANGUAGE) -> str:
    normalized = _normalize_string(lang).lower()
    return normalized if normalized in SUPPORTED_LANGUAGES else default


def _normalize_recent_path(path) -> str:
    normalized = _normalize_string(path)
    if not normalized:
        return ""
    return os.path.normpath(os.path.abspath(normalized))


def normalize_recent_files(recent_files, limit: int | None = DEFAULT_RECENT_LIMIT) -> list[str]:
    if limit is not None and limit <= 0:
        return []
    if not isinstance(recent_files, (list, tuple)):
        return []

    normalized_files: list[str] = []
    seen: set[str] = set()
    for item in recent_files:
        normalized_path = _normalize_recent_path(item)
        if not normalized_path:
            continue

        dedupe_key = os.path.normcase(normalized_path)
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        normalized_files.append(normalized_path)

        if limit is not None and len(normalized_files) >= limit:
            break

    return normalized_files


@dataclass
class AppSettings:
    input: str = ""
    output: str = ""
    dark: bool = False
    lang: str = DEFAULT_LANGUAGE
    recent: list[str] = field(default_factory=list)
    template: str = DEFAULT_TEMPLATE
    epub_input: str = ""
    epub_output: str = ""
    epub_paper: str = DEFAULT_EPUB_PAPER


def load_app_settings(path: str) -> AppSettings:
    if not path or not os.path.exists(path):
        return AppSettings()

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        return AppSettings()

    if not isinstance(data, dict):
        return AppSettings()

    default_settings = AppSettings()
    return AppSettings(
        input=_normalize_string(data.get("input"), default_settings.input),
        output=_normalize_string(data.get("output"), default_settings.output),
        dark=bool(data.get("dark", False)),
        lang=normalize_language(data.get("lang"), default_settings.lang),
        recent=normalize_recent_files(data.get("recent"), DEFAULT_RECENT_LIMIT),
        template=_normalize_string(data.get("template"), default_settings.template),
        epub_input=_normalize_string(data.get("epub_input"), default_settings.epub_input),
        epub_output=_normalize_string(data.get("epub_output"), default_settings.epub_output),
        epub_paper=_normalize_string(data.get("epub_paper"), default_settings.epub_paper),
    )


def save_app_settings(path: str, settings: AppSettings):
    if not path:
        return

    data = {
        "input": _normalize_string(settings.input),
        "output": _normalize_string(settings.output),
        "dark": settings.dark,
        "lang": normalize_language(settings.lang),
        "recent": normalize_recent_files(settings.recent, DEFAULT_RECENT_LIMIT),
        "template": _normalize_string(settings.template, DEFAULT_TEMPLATE),
        "epub_input": _normalize_string(settings.epub_input),
        "epub_output": _normalize_string(settings.epub_output),
        "epub_paper": _normalize_string(settings.epub_paper, DEFAULT_EPUB_PAPER),
    }

    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except Exception:
        return


def push_recent_file(recent_files: list[str], path: str, limit: int = 8) -> list[str]:
    normalized_path = _normalize_recent_path(path)
    if not normalized_path:
        return normalize_recent_files(recent_files, limit)

    new_recent = [
        item
        for item in normalize_recent_files(recent_files, None)
        if os.path.normcase(item) != os.path.normcase(normalized_path)
    ]
    new_recent.insert(0, normalized_path)
    return normalize_recent_files(new_recent, limit)
