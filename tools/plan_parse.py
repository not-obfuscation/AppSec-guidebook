"""Разбор плана обучения в структуру этап → подраздел → тема.

План (по умолчанию `/home/tarchok/Obsidian Vault/AppSec-engineer/plan.md.md`,
переопределяется переменной окружения `APPSEC_PLAN_PATH`) — источник
истины по темам и порядку, документ только на чтение. Здесь он ни при каких
условиях не правится: файл открывается в режиме 'r' и разбирается.
"""

import os
import re
from pathlib import Path

# План лежит вне репозитория, на машине автора, поэтому путь к нему не
# зашит окончательно: переменная окружения APPSEC_PLAN_PATH, дефолт — путь
# на машине автора. Значит везде, где репозиторий проверяется без неё — в CI
# прежде всего, — плана нет и не будет. Проверки, которым он нужен, обязаны
# это заметить и сказать вслух, а не падать трассировкой и не молчать:
# см. `plan_missing_note()`.
PLAN_PATH = Path(os.environ.get(
    "APPSEC_PLAN_PATH", "/home/tarchok/Obsidian Vault/AppSec-engineer/plan.md.md"))

# Маркер, по которому `check.py` показывает пропуск даже у зелёной проверки:
# иначе «ok» без плана не отличить от «ok» со всеми проверками.
SKIP_MARK = "ПРОПУЩЕНО"
PLAN_NOTE = f"{SKIP_MARK}: плана нет — он вне репозитория, на машине автора"


def plan_available(path: Path = PLAN_PATH) -> bool:
    """Есть ли под рукой план обучения. Единственное место, где это решается."""
    return path.is_file()

# Этап 6 (российская нормативка) исключён из гайдбука решением оператора:
# источники по нему не собираются и покрытие по нему не требуется.
EXCLUDED_STAGES = {6}

RE_STAGE = re.compile(r"^##\s+ЭТАП\s+(\d+)\.\s*(.+?)\s*$")
RE_SUBSECTION = re.compile(r"^###\s+(.+?)\s*$")
RE_TOPIC = re.compile(r"^-\s+\[[ xX]\]\s+(.+?)\s*$")
RE_NUMBERED = re.compile(r"^(\d+\.\d+)\s+(.+)$")


def parse_plan(path: Path = PLAN_PATH) -> list[dict]:
    """Вернуть список этапов: [{num, title, excluded, subsections: [...]}].

    Темы, стоящие в этапе до первого `###`, складываются в псевдоподраздел
    с sub_num == номер этапа и пустым заголовком — так этапы без подразделов
    (0, 3, 5, 6, 8) и этапы с подразделами обрабатываются одинаково.
    """
    stages: list[dict] = []
    stage = None
    sub = None
    sub_index = 0

    for raw in path.read_text(encoding="utf-8").splitlines():
        m = RE_STAGE.match(raw)
        if m:
            num = int(m.group(1))
            stage = {
                "num": num,
                "title": m.group(2),
                "excluded": num in EXCLUDED_STAGES,
                "subsections": [],
            }
            stages.append(stage)
            sub = None
            sub_index = 0
            continue

        if stage is None:
            continue

        m = RE_SUBSECTION.match(raw)
        if m:
            sub_index += 1
            heading = m.group(1)
            mn = RE_NUMBERED.match(heading)
            if mn:
                sub_num, sub_title = mn.group(1), mn.group(2)
            else:
                # Подразделы этапа 7 названы без номеров («Python (основной…)»).
                sub_num, sub_title = f"{stage['num']}.{sub_index}", heading
            sub = {"num": sub_num, "title": sub_title, "topics": []}
            stage["subsections"].append(sub)
            continue

        m = RE_TOPIC.match(raw)
        if m:
            if sub is None:
                sub = {"num": str(stage["num"]), "title": "", "topics": []}
                stage["subsections"].append(sub)
            sub["topics"].append(m.group(1))

    return stages


def topic_id(stage_num: int, sub_num: str, order: int) -> str:
    """Стабильный id темы: t-<этап>-<подраздел>-<номер темы>.

    Подраздел в id — только его порядковый номер внутри этапа (или 0, если
    подразделов у этапа нет), чтобы id не зависел от заголовка.
    """
    tail = sub_num.split(".", 1)
    sub_part = tail[1] if len(tail) == 2 else "0"
    return f"t-{stage_num}-{sub_part}-{order:02d}"


def flat_topics(stages: list[dict]) -> list[dict]:
    """Плоский список тем со всеми ключами, нужными для сверки и покрытия."""
    out = []
    for stage in stages:
        for sub in stage["subsections"]:
            for i, title in enumerate(sub["topics"], start=1):
                out.append(
                    {
                        "id": topic_id(stage["num"], sub["num"], i),
                        "title": title,
                        "stage": stage["num"],
                        "stage_title": stage["title"],
                        "sub": sub["num"],
                        "sub_title": sub["title"],
                        "order": i,
                        "excluded": stage["excluded"],
                    }
                )
    return out


if __name__ == "__main__":
    stages = parse_plan()
    topics = flat_topics(stages)
    subs = sum(len(s["subsections"]) for s in stages)
    print(f"этапов: {len(stages)}, подразделов (с псевдо): {subs}, тем: {len(topics)}")
    for stage in stages:
        mark = " [исключён]" if stage["excluded"] else ""
        n = sum(len(s["topics"]) for s in stage["subsections"])
        print(f"  этап {stage['num']}: {n:3d} тем, {len(stage['subsections'])} подразд.{mark}")
