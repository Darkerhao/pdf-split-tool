import json
import os
from dataclasses import dataclass, field


@dataclass
class AppSettings:
    input: str = ""
    output: str = ""
    dark: bool = False
    lang: str = "zh"
    recent: list[str] = field(default_factory=list)
    template: str = "{name}_{start}-{end}.pdf"
    epub_input: str = ""
    epub_output: str = ""
    epub_paper: str = "a4"


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

    return AppSettings(
        input=data.get("input", "") or "",
        output=data.get("output", "") or "",
        dark=bool(data.get("dark", False)),
        lang=data.get("lang", "zh") or "zh",
        recent=list(data.get("recent", []) or []),
        template=data.get("template", "{name}_{start}-{end}.pdf") or "{name}_{start}-{end}.pdf",
        epub_input=data.get("epub_input", "") or "",
        epub_output=data.get("epub_output", "") or "",
        epub_paper=data.get("epub_paper", "a4") or "a4",
    )


def save_app_settings(path: str, settings: AppSettings):
    if not path:
        return

    data = {
        "input": settings.input,
        "output": settings.output,
        "dark": settings.dark,
        "lang": settings.lang,
        "recent": settings.recent,
        "template": settings.template,
        "epub_input": settings.epub_input,
        "epub_output": settings.epub_output,
        "epub_paper": settings.epub_paper,
    }

    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except Exception:
        return


def push_recent_file(recent_files: list[str], path: str, limit: int = 8) -> list[str]:
    if not path:
        return list(recent_files)

    normalized_path = os.path.abspath(path)
    new_recent = [item for item in recent_files if item != normalized_path]
    new_recent.insert(0, normalized_path)
    return new_recent[:limit]
