"""Валидатор реестра источников и покрытия тем.

Он же — критерий готовности миссии: пока он не зелёный, реестр не собран.

    python tools/validate.py            # полная проверка
    python tools/validate.py --stage 0  # только один этап (покрытие)
    python tools/validate.py --quiet    # только итог и ошибки

Проверки делятся на блокирующие (ошибка → выход 1) и предупреждающие
(выход 0). Блокирующие:

  СХЕМА     — каждая запись sources.yaml валидна по схеме части 9 плейбука;
  ССЫЛКИ    — каждый id из topics.yaml разрешается в реестре;
  ПЛАН      — структура topics.yaml совпадает с планом обучения;
  ПОКРЫТИЕ  — у каждой темы этапов 0–5, 7, 8 есть хотя бы один источник
              со статусом ok (needs_manual_check покрытием не считается).

Правило «1–3 источника на тему» относится к собственным источникам темы.
Наследуемое от этапа и подраздела в лимит не входит: это общий каркас, который
по решению автора заводится один раз на своём уровне, а тема добавляет поверх
него свою специфику.
"""

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from plan_parse import PLAN_NOTE, parse_plan, plan_available, topic_id
from paths import SOURCES_YAML, TOPICS_YAML

# --- словари схемы -----------------------------------------------------------

TYPES = {
    "spec",            # RFC, W3C/WHATWG standard — уровень 1
    "official-docs",   # документация вендора/проекта
    "tool-docs",       # документация инструмента
    "standard",        # ASVS, NIST SP и т.п.
    "owasp",           # материалы OWASP вне ASVS
    "reference-db",    # CWE, CVE, KEV, EPSS
    "course",          # учебная платформа с практикой
    "book",            # книга-эталон
    "research",        # оригинальная публикация
    "regulation",      # нормативный акт
}
VOLATILITY = {"stable", "medium", "fast"}
STATUS = {"ok", "needs_manual_check"}
LEVELS = {1, 2, 3, 4, 5}

REQUIRED = [
    "id", "url", "title", "type", "level", "publisher",
    "version_or_date", "volatility", "license", "checked", "status",
]
OPTIONAL = {"notes", "archived_url"}

RE_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RE_URL = re.compile(r"^https?://\S+$")

# Уровень авторитетности, ожидаемый для типа (раздел «Критерий авторитетности»
# journal/SOURCES.md). Несовпадение — предупреждение, а не ошибка: бывают исключения,
# но каждое должно быть замечено.
EXPECTED_LEVEL = {
    "spec": 1, "official-docs": 1, "tool-docs": 1, "regulation": 1,
    "standard": 2, "owasp": 2, "reference-db": 2,
    "course": 3, "book": 4, "research": 5,
}

# Домены, которые источником не считаются (раздел «Критерий авторитетности»).
BANNED_HOSTS = ("hacktricks.", "medium.com", "howtoharden.com")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, kind: str, msg: str) -> None:
        self.errors.append(f"[{kind}] {msg}")

    def warn(self, kind: str, msg: str) -> None:
        self.warnings.append(f"[{kind}] {msg}")


def load_yaml(path: Path, rep: Report) -> dict:
    if not path.exists():
        rep.error("ФАЙЛ", f"{path.name} не найден")
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        rep.error("ФАЙЛ", f"{path.name} не разбирается как YAML: {exc}")
        return {}


# --- проверка реестра --------------------------------------------------------

def check_sources(data: dict, rep: Report, today: dt.date) -> dict[str, dict]:
    entries = data.get("sources")
    if entries is None:
        rep.error("СХЕМА", "в sources.yaml нет ключа верхнего уровня `sources`")
        return {}
    if not isinstance(entries, list):
        rep.error("СХЕМА", "`sources` в sources.yaml должен быть списком")
        return {}

    by_id: dict[str, dict] = {}
    by_url: dict[str, str] = {}

    for i, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            rep.error("СХЕМА", f"запись #{i} — не словарь")
            continue
        sid = entry.get("id", f"<запись #{i}>")

        for field in REQUIRED:
            value = entry.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                rep.error("СХЕМА", f"{sid}: не заполнено обязательное поле `{field}`")
        unknown = set(entry) - set(REQUIRED) - OPTIONAL
        if unknown:
            rep.error("СХЕМА", f"{sid}: поля вне схемы: {', '.join(sorted(unknown))}")

        if isinstance(sid, str) and not RE_ID.match(sid):
            rep.error("СХЕМА", f"{sid}: id не в kebab-case")
        if sid in by_id:
            rep.error("СХЕМА", f"{sid}: дубль id в реестре")
        else:
            by_id[sid] = entry

        url = entry.get("url")
        if isinstance(url, str):
            if not RE_URL.match(url):
                rep.error("СХЕМА", f"{sid}: url не похож на http(s)-адрес: {url}")
            if url in by_url:
                rep.error("СХЕМА", f"{sid}: тот же url, что у {by_url[url]} — сведите к одной записи")
            else:
                by_url[url] = sid
            if any(host in url for host in BANNED_HOSTS):
                rep.error("СХЕМА", f"{sid}: {url} — источником не считается (агрегатор/Medium)")

        stype = entry.get("type")
        if stype is not None and stype not in TYPES:
            rep.error("СХЕМА", f"{sid}: неизвестный type `{stype}`")
        level = entry.get("level")
        if level is not None and level not in LEVELS:
            rep.error("СХЕМА", f"{sid}: level должен быть целым 1–5, а не `{level}`")
        if stype in EXPECTED_LEVEL and level in LEVELS and level != EXPECTED_LEVEL[stype]:
            rep.warn("УРОВЕНЬ", f"{sid}: type `{stype}` обычно уровня {EXPECTED_LEVEL[stype]}, стоит {level}")
        vol = entry.get("volatility")
        if vol is not None and vol not in VOLATILITY:
            rep.error("СХЕМА", f"{sid}: volatility должна быть stable/medium/fast, а не `{vol}`")
        status = entry.get("status")
        if status is not None and status not in STATUS:
            rep.error("СХЕМА", f"{sid}: status должен быть ok/needs_manual_check, а не `{status}`")
        if status == "needs_manual_check" and not str(entry.get("notes") or "").strip():
            rep.error("СХЕМА", f"{sid}: needs_manual_check без объяснения в `notes`")

        checked = entry.get("checked")
        if checked is not None:
            if isinstance(checked, dt.datetime):
                checked = checked.date()
            if isinstance(checked, dt.date):
                if checked > today:
                    rep.error("СХЕМА", f"{sid}: дата проверки {checked} в будущем")
            else:
                rep.error("СХЕМА", f"{sid}: `checked` должна быть датой YYYY-MM-DD, а не `{checked}`")

    return by_id


# --- проверка карты тем ------------------------------------------------------

def check_topics_match_plan(data: dict, rep: Report) -> None:
    """Структура topics.yaml обязана совпадать с планом один в один.

    Без плана проверка не выполняется и об этом печатается строка. Сверять
    `topics.yaml` не с чем: он и есть проекция плана, и сравнение его с собой
    ничего не значит. Отсутствие плана — не ошибка реестра, поэтому в `rep`
    оно не попадает; но и молча пропасть проверка не имеет права.
    """
    if not plan_available():
        print(f"ПЛАН — {PLAN_NOTE}")
        return

    expected = []
    for stage in parse_plan():
        for sub in stage["subsections"]:
            for i, title in enumerate(sub["topics"], start=1):
                expected.append((topic_id(stage["num"], sub["num"], i), title))

    actual = []
    for stage in data.get("stages") or []:
        for sub in stage.get("subsections") or []:
            for topic in sub.get("topics") or []:
                actual.append((topic.get("id"), topic.get("title")))

    if expected != actual:
        exp, act = set(expected), set(actual)
        for item in sorted(exp - act)[:5]:
            rep.error("ПЛАН", f"темы нет в topics.yaml: {item[0]} «{item[1]}»")
        for item in sorted(act - exp)[:5]:
            rep.error("ПЛАН", f"тема в topics.yaml не из плана: {item[0]} «{item[1]}»")
        if exp == act:
            rep.error("ПЛАН", "порядок тем в topics.yaml разошёлся с планом")
        rep.error("ПЛАН", "прогоните `python tools/gen_topics.py` — она перенесёт sources")


def collect(data: dict, by_id: dict[str, dict], rep: Report) -> list[dict]:
    """Плоский список тем с уже разрешённым наследованием источников."""
    seen_refs: set[str] = set()
    topics: list[dict] = []

    def refs(node: dict, where: str) -> list[str]:
        ids = node.get("sources") or []
        if not isinstance(ids, list):
            rep.error("ССЫЛКИ", f"{where}: `sources` должен быть списком id")
            return []
        out = []
        for sid in ids:
            seen_refs.add(sid)
            if sid not in by_id:
                rep.error("ССЫЛКИ", f"{where}: id `{sid}` не найден в sources.yaml")
            else:
                out.append(sid)
        return out

    for stage in data.get("stages") or []:
        num = stage.get("num")
        stage_ids = refs(stage, f"этап {num}")
        for sub in stage.get("subsections") or []:
            sub_num = sub.get("num")
            sub_ids = refs(sub, f"подраздел {sub_num}")
            for topic in sub.get("topics") or []:
                tid = topic.get("id")
                own = refs(topic, f"тема {tid}")
                dup = set(own) & (set(stage_ids) | set(sub_ids))
                if dup:
                    rep.error(
                        "ССЫЛКИ",
                        f"тема {tid}: {', '.join(sorted(dup))} уже наследуется от этапа/подраздела "
                        "— дубль вместо наследования запрещён",
                    )
                effective = list(dict.fromkeys(stage_ids + sub_ids + own))
                topics.append(
                    {
                        "id": tid,
                        "title": topic.get("title"),
                        "stage": num,
                        "sub": sub_num,
                        "excluded": bool(stage.get("excluded")),
                        "effective": effective,
                        "own": own,
                        "working_set": list(dict.fromkeys(sub_ids + own)),
                    }
                )

    for sid in sorted(set(by_id) - seen_refs):
        rep.warn("СИРОТА", f"{sid}: запись в реестре, на которую не ссылается ни одна тема")
    return topics


def check_coverage(topics: list[dict], by_id: dict[str, dict], rep: Report,
                   only_stage: int | None) -> dict[int, tuple[int, int]]:
    per_stage: dict[int, tuple[int, int]] = {}
    for topic in topics:
        if topic["excluded"]:
            continue
        stage = topic["stage"]
        if only_stage is not None and stage != only_stage:
            continue
        usable = [s for s in topic["effective"] if by_id.get(s, {}).get("status") == "ok"]
        done, total = per_stage.get(stage, (0, 0))
        per_stage[stage] = (done + (1 if usable else 0), total + 1)
        if not usable:
            pending = [s for s in topic["effective"] if s not in usable]
            hint = f" (есть только needs_manual_check: {', '.join(pending)})" if pending else ""
            rep.error("ПОКРЫТИЕ", f"тема {topic['id']} «{topic['title']}» без источника{hint}")
        elif not [s for s in topic["working_set"] if by_id.get(s, {}).get("status") == "ok"]:
            rep.warn(
                "КАРКАС",
                f"тема {topic['id']} держится только на источниках уровня этапа — у неё нет ни "
                "своего источника, ни источника подраздела",
            )
        elif len(topic["own"]) > 3:
            rep.warn(
                "ГЛУБИНА",
                f"тема {topic['id']}: {len(topic['own'])} собственных источников — больше трёх "
                "берут только тогда, когда после трёх остался незакрытый блок скелета",
            )
    return per_stage


def main() -> int:
    ap = argparse.ArgumentParser(description="Валидатор реестра источников")
    ap.add_argument("--stage", type=int, default=None, help="проверять покрытие только этого этапа")
    ap.add_argument("--quiet", action="store_true", help="без сводки по этапам")
    args = ap.parse_args()

    rep = Report()
    today = dt.date.today()

    sources_data = load_yaml(SOURCES_YAML, rep)
    topics_data = load_yaml(TOPICS_YAML, rep)
    by_id = check_sources(sources_data, rep, today)
    check_topics_match_plan(topics_data, rep)
    topics = collect(topics_data, by_id, rep)
    per_stage = check_coverage(topics, by_id, rep, args.stage)

    if not args.quiet:
        print(f"Реестр: {len(by_id)} записей, из них ok: "
              f"{sum(1 for e in by_id.values() if e.get('status') == 'ok')}")
        print("Покрытие по этапам (темы с источником / всего):")
        for stage in sorted(per_stage):
            done, total = per_stage[stage]
            bar = "█" * round(20 * done / total) if total else ""
            print(f"  этап {stage}: {done:3d}/{total:3d}  {bar}")
        print("  этап 6: исключён из гайдбука решением оператора")

    for msg in rep.warnings:
        print(f"ПРЕДУПРЕЖДЕНИЕ {msg}")
    for msg in rep.errors:
        print(f"ОШИБКА {msg}")

    # Приписка в вердикте, чтобы «зелёный» без плана нельзя было спутать с
    # «зелёный со всеми проверками».
    tail = "" if plan_available() else ", проверка плана не выполнялась"

    if rep.errors:
        print(f"\nВАЛИДАТОР: КРАСНЫЙ — {len(rep.errors)} ошибок, "
              f"{len(rep.warnings)} предупреждений{tail}")
        return 1
    print(f"\nВАЛИДАТОР: ЗЕЛЁНЫЙ — 0 ошибок, "
          f"{len(rep.warnings)} предупреждений{tail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
