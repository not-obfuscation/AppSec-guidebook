"""Генерация topics.yaml из плана обучения.

topics.yaml — карта «этап → подраздел → тема → sources: [id]». Структура
(этапы, подразделы, темы, порядок) целиком выводится из плана и руками не
правится; руками правятся только списки `sources`. При перегенерации
существующие привязки переносятся по заголовку темы — так вставка новой темы
в план не сбрасывает уже собранные источники.

Привязка гибридная: источник, закрывающий весь этап или подраздел, кладётся в
`sources` этапа/подраздела и наследуется его темами. Дублировать одну запись
во всех темах подраздела запрещено — при выборе между дублем и наследованием
всегда наследование.

    python tools/gen_topics.py [--check]

--check ничего не пишет, а сообщает, разошёлся ли topics.yaml с планом.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from plan_parse import PLAN_NOTE, PLAN_PATH, parse_plan, plan_available, topic_id

ROOT = Path(__file__).resolve().parent.parent
TOPICS_PATH = ROOT / "topics.yaml"

HEADER = """\
# Карта тем гайдбука: этап → подраздел → тема → sources.
#
# ФАЙЛ ГЕНЕРИРУЕТСЯ: `python tools/gen_topics.py`. Структура выводится из плана
# обучения и правится только там (план — документ оператора, агент его не
# трогает). Руками здесь правятся ТОЛЬКО списки `sources` — они переживают
# перегенерацию, потому что переносятся по заголовку темы.
#
# Источник уровня этапа или подраздела наследуется всеми темами внутри —
# дублировать его в каждой теме не нужно и запрещено.
#
# Этап 6 (российская нормативная база) исключён из гайдбука решением
# оператора: excluded: true, источники по нему не собираются.
"""


def quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def fmt_sources(ids: list[str], indent: str) -> str:
    if not ids:
        return f"{indent}sources: []\n"
    return f"{indent}sources: [{', '.join(ids)}]\n"


def load_existing() -> dict[tuple[str, str], list[str]]:
    """Карта (подраздел, заголовок темы) → sources из текущего topics.yaml.

    Ключи уровня этапа и подраздела хранятся как (номер, "") и ("", номер),
    чтобы не пересечься с темами.
    """
    if not TOPICS_PATH.exists():
        return {}
    data = yaml.safe_load(TOPICS_PATH.read_text(encoding="utf-8")) or {}
    out: dict[tuple[str, str], list[str]] = {}
    for stage in data.get("stages") or []:
        out[(str(stage.get("num")), "")] = list(stage.get("sources") or [])
        for sub in stage.get("subsections") or []:
            sub_num = str(sub.get("num"))
            out[("", sub_num)] = list(sub.get("sources") or [])
            for topic in sub.get("topics") or []:
                out[(sub_num, str(topic.get("title")))] = list(topic.get("sources") or [])
    return out


def render(stages: list[dict], existing: dict[tuple[str, str], list[str]]) -> str:
    out = [HEADER, "\n", f"generated_from: {quote(str(PLAN_PATH))}\n", "\nstages:\n"]
    for stage in stages:
        out.append(f"  - num: {stage['num']}\n")
        out.append(f"    title: {quote(stage['title'])}\n")
        out.append(f"    excluded: {str(stage['excluded']).lower()}\n")
        out.append(fmt_sources(existing.get((str(stage["num"]), ""), []), "    "))
        out.append("    subsections:\n")
        for sub in stage["subsections"]:
            out.append(f"      - num: {quote(sub['num'])}\n")
            out.append(f"        title: {quote(sub['title'])}\n")
            out.append(fmt_sources(existing.get(("", sub["num"]), []), "        "))
            out.append("        topics:\n")
            for i, title in enumerate(sub["topics"], start=1):
                out.append(f"          - id: {topic_id(stage['num'], sub['num'], i)}\n")
                out.append(f"            title: {quote(title)}\n")
                out.append(fmt_sources(existing.get((sub["num"], title), []), "            "))
    return "".join(out)


def main() -> int:
    check = "--check" in sys.argv[1:]

    # Без плана генерировать не из чего и сверять не с чем. Для `--check` это
    # не отказ: `topics.yaml` — проекция плана, и сравнивать его с собой
    # бессмысленно. А вот запись без плана — именно отказ, иначе `topics.yaml`
    # молча перезапишется пустым.
    if not plan_available():
        print(f"topics.yaml — {PLAN_NOTE}")
        return 0 if check else 1

    text = render(parse_plan(), load_existing())
    if check:
        current = TOPICS_PATH.read_text(encoding="utf-8") if TOPICS_PATH.exists() else ""
        if current != text:
            print("topics.yaml разошёлся с планом — прогоните: python tools/gen_topics.py")
            return 1
        print("topics.yaml соответствует плану")
        return 0
    TOPICS_PATH.write_text(text, encoding="utf-8")
    n = sum(len(s["topics"]) for st in parse_plan() for s in st["subsections"])
    print(f"topics.yaml записан: {n} тем")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
