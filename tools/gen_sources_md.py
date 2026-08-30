"""Генерация человекочитаемых файлов по этапам из sources.yaml + topics.yaml.

    python tools/gen_sources_md.py

Пишет `sources/этап-N.md` для каждого невыключенного этапа и `sources/README.md`
со сводкой. ЭТИ ФАЙЛЫ НЕ ПРАВЯТСЯ РУКАМИ: источник истины — YAML, любая правка
markdown будет затёрта следующей генерацией.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from paths import ROOT

OUT_DIR = ROOT / "sources"

LEVEL_NAME = {
    1: "первоисточник",
    2: "отраслевой консенсус",
    3: "учебный ресурс",
    4: "книга-эталон",
    5: "исследование",
}
VOL_NAME = {"stable": "стабилен", "medium": "средне", "fast": "быстро"}

BANNER = (
    "<!-- ФАЙЛ СГЕНЕРИРОВАН: python tools/gen_sources_md.py\n"
    "     Источник истины — sources.yaml и topics.yaml. Правки здесь будут затёрты. -->\n"
)


def load(name: str) -> dict:
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8")) or {}


def entry_line(e: dict) -> str:
    flag = "" if e.get("status") == "ok" else " ⚠ требует ручной проверки"
    return (
        f"| [{e['title']}]({e['url']}) | {e['type']} · L{e['level']} "
        f"{LEVEL_NAME.get(e['level'], '')} | {e['publisher']} | {e['version_or_date']} | "
        f"{VOL_NAME.get(e['volatility'], e['volatility'])} | {e['license']} | {e['checked']}{flag} |"
    )


def render_stage(stage: dict, by_id: dict[str, dict]) -> str:
    num, title = stage["num"], stage["title"]
    out = [BANNER, f"\n# Этап {num}. {title}\n\n"]

    stage_ids = list(stage.get("sources") or [])
    if stage_ids:
        out.append("## Ядро этапа\n\n")
        out.append("Источники, наследуемые всеми темами этапа — их открывают первыми.\n\n")
        out.append(TABLE_HEAD)
        out += [entry_line(by_id[s]) + "\n" for s in stage_ids]
        out.append("\n")

    for sub in stage.get("subsections") or []:
        heading = f"{sub['num']} {sub['title']}".strip() if sub["title"] else "Темы этапа"
        out.append(f"## {heading}\n\n")
        sub_ids = list(sub.get("sources") or [])
        if sub_ids:
            out.append("Наследуется всеми темами подраздела:\n\n")
            out.append(TABLE_HEAD)
            out += [entry_line(by_id[s]) + "\n" for s in sub_ids]
            out.append("\n")
        for topic in sub.get("topics") or []:
            own = list(topic.get("sources") or [])
            inherited = stage_ids + sub_ids
            out.append(f"### {topic['title']}\n\n")
            out.append(f"`{topic['id']}`\n\n")
            if own:
                out.append(TABLE_HEAD)
                out += [entry_line(by_id[s]) + "\n" for s in own]
                out.append("\n")
            elif inherited:
                out.append(f"Своих источников нет — закрывается наследуемыми: "
                           f"{', '.join(f'`{s}`' for s in inherited)}.\n\n")
            else:
                out.append("**Источников пока нет.**\n\n")
            notes = [by_id[s].get("notes") for s in own if by_id[s].get("notes")]
            for note in notes:
                out.append(f"> {note}\n\n")
    return "".join(out)


TABLE_HEAD = (
    "| Источник | Тип · уровень | Издатель | Версия / дата | Гниёт | Лицензия | Проверен |\n"
    "|---|---|---|---|---|---|---|\n"
)


def main() -> int:
    sources = {e["id"]: e for e in (load("sources.yaml").get("sources") or [])}
    topics = load("topics.yaml")
    OUT_DIR.mkdir(exist_ok=True)

    summary = [BANNER, "\n# Источники по этапам\n\n",
               "Сгенерировано из `sources.yaml` и `topics.yaml`.\n\n",
               "| Этап | Тем | С источником | Файл |\n|---|---|---|---|\n"]

    written = 0
    for stage in topics.get("stages") or []:
        if stage.get("excluded"):
            summary.append(f"| {stage['num']}. {stage['title']} | — | исключён из гайдбука | — |\n")
            continue
        inherited = list(stage.get("sources") or [])
        total = covered = 0
        for sub in stage.get("subsections") or []:
            sub_ids = inherited + list(sub.get("sources") or [])
            for topic in sub.get("topics") or []:
                total += 1
                eff = sub_ids + list(topic.get("sources") or [])
                if any(sources.get(s, {}).get("status") == "ok" for s in eff):
                    covered += 1
        path = OUT_DIR / f"этап-{stage['num']}.md"
        path.write_text(render_stage(stage, sources), encoding="utf-8")
        written += 1
        summary.append(f"| {stage['num']}. {stage['title']} | {total} | {covered} | "
                       f"[{path.name}]({path.name}) |\n")

    (OUT_DIR / "README.md").write_text("".join(summary), encoding="utf-8")
    print(f"sources/: записано {written} файлов по этапам + README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
