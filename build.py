#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — пересборка index.html из исходников.

Использование:
    python3 build.py            — пересобрать всё
    python3 build.py --prompt   — пересобрать только SYSTEM_PROMPT
    python3 build.py --replies  — пересобрать только DI_REPLIES
    python3 build.py --assets   — пересобрать только ASSETS

Источники:
    system_prompt.md     — текст системного промпта для LLM
    replies_mapping.md   — таблица фирменных фраз Димы
    avatars/avatar_*.jpeg — изображения для встраивания в Base64

В index.html должны быть маркеры (расставлены автоматически при первой
сборке): /* ASSETS_BEGIN */ ... /* ASSETS_END */, аналогично для
DI_REPLIES и SYSTEM_PROMPT.
"""

import sys
import re
import json
import base64
import pathlib
import argparse

ROOT = pathlib.Path(__file__).parent.resolve()

INDEX_PATH       = ROOT / "index.html"
PROMPT_PATH      = ROOT / "system_prompt.md"
REPLIES_PATH     = ROOT / "replies_mapping.md"
AVATARS_DIR      = ROOT / "avatars"


def fail(msg: str) -> None:
    print(f"[build] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def patch_block(html: str, marker: str, new_body: str) -> str:
    """Заменить содержимое блока между /* {marker}_BEGIN ... */ и /* {marker}_END */."""
    pattern = re.compile(
        r"(/\*\s*" + re.escape(marker) + r"_BEGIN[^*]*\*/\s*\n)"
        r"([\s\S]*?)"
        r"(\n\s*/\*\s*" + re.escape(marker) + r"_END\s*\*/)",
        re.MULTILINE,
    )
    if not pattern.search(html):
        fail(f"маркер {marker}_BEGIN/{marker}_END не найден в index.html")
    return pattern.sub(lambda m: m.group(1) + new_body + m.group(3), html, count=1)


# ----------------------------- builders --------------------------------

def build_system_prompt() -> str:
    if not PROMPT_PATH.exists():
        fail(f"не найден {PROMPT_PATH}")
    text = PROMPT_PATH.read_text(encoding="utf-8")
    # JSON-encode → безопасная JS-строка с \n, кавычками, юникодом
    js_string = json.dumps(text, ensure_ascii=False)
    return f"const SYSTEM_PROMPT = {js_string};"


def _parse_trigger_table(prompt_text: str):
    """Парсит markdown-таблицу из system_prompt.md.
    Возвращает список dict-ов: {id, text, avatar, emotion, triggers[]}.
    Если таблицы нет — вернёт [].
    """
    rows = []
    in_table = False
    for raw_line in prompt_text.splitlines():
        line = raw_line.rstrip()
        if not line.startswith("|"):
            in_table = False
            continue
        # шапка таблицы
        if re.search(r"\|\s*Line\s*\|", line, re.IGNORECASE):
            in_table = True
            continue
        # разделитель |---|---|
        if set(line.replace("|", "").replace(":", "").strip()) <= {"-", " "}:
            continue
        if not in_table:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        try:
            line_id = int(cells[0])
        except ValueError:
            continue
        text = cells[1].strip()
        # убираем лишние пробелы в тексте, если есть (формат таблицы кривоват)
        text = re.sub(r"\s+", " ", text).strip()
        avatar_m = re.search(r"avatar_\d+\.jpeg", cells[2])
        avatar = avatar_m.group(0) if avatar_m else "avatar_2.jpeg"
        emotion = re.sub(r"<[^>]+>", "", cells[3]).strip()
        triggers_cell = cells[4]
        triggers = []
        # 1) фразы в «...»
        for m in re.finditer(r"«([^»]+)»", triggers_cell):
            phrase = m.group(1).strip()
            if phrase:
                triggers.append(phrase)
        # 2) описания в скобках после ID: "2 (Ты успел?)"
        for m in re.finditer(r"\d+\s*\(([^)]+)\)", triggers_cell):
            phrase = m.group(1).strip()
            # отфильтруем мета-описания типа "контекст: ..."
            if phrase and "контекст" not in phrase.lower():
                triggers.append(phrase)
        # удаляем дубликаты, сохраняем порядок
        seen, dedup = set(), []
        for t in triggers:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                dedup.append(t)
        rows.append({
            "id": line_id,
            "text": text,
            "avatar": avatar,
            "emotion": emotion,
            "triggers": dedup,
        })
    return rows


def build_di_replies() -> str:
    """Источник #1: trigger-таблица в system_prompt.md.
    Источник #2 (fallback): replies_mapping.md без триггеров.
    """
    replies = []
    if PROMPT_PATH.exists():
        prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
        replies = _parse_trigger_table(prompt_text)

    if not replies:
        # legacy-парсер
        if not REPLIES_PATH.exists():
            fail("ни system_prompt.md (с таблицей), ни replies_mapping.md не найдены")
        lines = REPLIES_PATH.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if not line.startswith("|"):
                continue
            if "Line #" in line or set(line.replace("|", "").replace(":", "").strip()) <= {"-", " "}:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 4:
                continue
            try:
                idx = int(cells[0])
            except ValueError:
                continue
            text = cells[1]
            m = re.search(r"avatar_\d+\.jpeg", cells[2])
            avatar = m.group(0) if m else "avatar_2.jpeg"
            emotion = re.sub(r"<[^>]+>", "", cells[3])
            emotion = re.sub(r"^В+нимательный$", "Внимательный", emotion)
            replies.append({"id": idx, "text": text, "avatar": avatar,
                            "emotion": emotion, "triggers": []})

    if not replies:
        fail("не удалось извлечь ни одной реплики ни из system_prompt.md, ни из replies_mapping.md")
    print(f"[build] DI_REPLIES: {len(replies)} строк")
    body = "const DI_REPLIES = " + json.dumps(replies, ensure_ascii=False, indent=2) + ";"
    return body


def build_assets() -> str:
    if not AVATARS_DIR.exists():
        fail(f"не найден каталог {AVATARS_DIR}")
    parts = ["const ASSETS = {"]
    found = sorted(AVATARS_DIR.glob("avatar_*.jpeg"),
                   key=lambda p: int(re.search(r"\d+", p.stem).group(0)))
    if not found:
        fail("в avatars/ нет файлов avatar_*.jpeg")
    for p in found:
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        parts.append(f'  "{p.name}": "data:image/jpeg;base64,{b64}",')
    parts.append("};")
    return "\n".join(parts)


# ----------------------------- main ------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Пересборка index.html")
    parser.add_argument("--prompt",  action="store_true", help="только SYSTEM_PROMPT")
    parser.add_argument("--replies", action="store_true", help="только DI_REPLIES")
    parser.add_argument("--assets",  action="store_true", help="только ASSETS")
    args = parser.parse_args()

    do_all = not (args.prompt or args.replies or args.assets)

    if not INDEX_PATH.exists():
        fail(f"не найден {INDEX_PATH}")

    html = INDEX_PATH.read_text(encoding="utf-8")
    changed = []

    if do_all or args.prompt:
        html = patch_block(html, "SYSTEM_PROMPT", build_system_prompt())
        changed.append("SYSTEM_PROMPT")
    if do_all or args.replies:
        html = patch_block(html, "DI_REPLIES", build_di_replies())
        changed.append("DI_REPLIES")
    if do_all or args.assets:
        html = patch_block(html, "ASSETS", build_assets())
        changed.append("ASSETS")

    INDEX_PATH.write_text(html, encoding="utf-8")
    size_kb = INDEX_PATH.stat().st_size / 1024
    print(f"[build] обновлены блоки: {', '.join(changed)}")
    print(f"[build] index.html → {size_kb:.1f} КБ")


if __name__ == "__main__":
    main()
