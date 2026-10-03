#!/usr/bin/env python3
"""Состав блока «Проверь себя» против правил 23–24 и 35: отчёт и вердикт гейта.

    python tools/selfcheck_report.py                     # сводка по корпусу
    python tools/selfcheck_report.py --full              # и по каждой теме
    python tools/selfcheck_report.py --verdict           # код возврата — вердикт

Решение оператора 2026-10-01 (реестр RN-05, RN-08): самопроверка проверяет
понимание, а не воспроизведение; возврат может целить любую более раннюю тему.
Новые требования — правила 23–24 и 35 `research/09-novice-delivery.md`:

  23  у темы-уязвимости есть вопрос с выбором: три варианта (четвёртый при
      четвёртом подтверждённом заблуждении), разбор каждого варианта под
      `<details>`, без «всё / ничего из перечисленного»;
  24  не меньше двух вопросов показывают фрагмент кода, HTTP-сообщения или
      конфига, хотя бы один новый для темы; есть вопрос «почему» и вопрос на
      предсказание; «что называет документ X» — только если документ и есть
      предмет темы;
  35  у тем L1 и L2 со этапа 2 есть возврат на другой этап.

Корпус переписан под эти правила, и запись в `tools/check.py` перенесена из
отчётов в реестр с флагом `--verdict`: состав блока ломает сборку, как
остальная схема (9.1). Флаг возвращает 1, если нарушена машинно-проверяемая
часть правил (фрагменты правила 24, вопрос с выбором правила 23 у
тем-уязвимостей и тем-заходов пороговых концепций, дальний возврат правила
35). Каркас блока (ответы под `<details>`, их число равно числу вопросов,
цель возврата раньше по маршруту) по-прежнему проверяет с вердиктом
`validate_content.py`.

Что машина видит, а что нет. Фрагмент — ограждённый блок кода внутри вопроса;
«новый для темы» — его текст не встречается в теме выше блока. Варианты
опознаются по строкам вида «A. …» / «Б) …» внутри вопроса. Счётчики «почему»,
«предсказание» и «называет документ» — эвристики для глаз (по ним вердикта нет
и в `--verdict`): отличить перечень от понимания машина не умеет, это часть
правила 24 с пометкой [Г]. Заходы пороговых концепций размечены в
`thresholds.yaml` (карточка RN-11): тема-заход обязана иметь вопрос с выбором
наравне с темой-уязвимостью, независимо от своего скелета.

Выход всегда 0 без `--verdict`; с ним — 1 при первом же нарушении.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mdtext
import validate_content as vc
from paths import ROOT

# Строка-вариант вопроса с выбором: «A. …», «Б) …». Букв не больше четырёх:
# правило 23 разрешает четвёртый вариант только при четвёртом заблуждении.
VARIANT_RE = re.compile(r"^\s{0,3}(?P<letter>[A-DА-Г])[.)]\s+\S")
CATCHALL_RE = re.compile(r"^\s{0,3}[A-DА-Г][.)]\s*"
                         r"(?:Вс[её]|Ничего|Ни одно|Все)\b.*\bперечислен",
                         re.I)
DETAILS_RE = re.compile(r"<details[^>]*>(.*?)</details>", re.S)
SUMMARY_RE = re.compile(r"<summary[^>]*>(.*?)</summary>", re.S)
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
INLINE_RE = re.compile(r"`[^`\n]+`")
# Эвристики для глаз (пометка [Г] у правила 24): машина считает, человек решает.
WHY_RE = re.compile(r"\bпочему\b", re.I)
PREDICT_RE = re.compile(r"\b(?:предскаж|что (?:будет|произойд[её]т|получится|"
                        r"ответит|верн[её]т|отправит|приложит))", re.I)
DOC_SAYS_RE = re.compile(r"\b(?:называет|предписывает|требует)\b", re.I)


def approach_topics() -> dict[str, list[str]]:
    """Темы-заходы пороговых концепций: `id` темы → список концепций.

    Разметка П1–П6 лежит в `thresholds.yaml`, а не в `topics.yaml`: план
    генерируется (`gen_topics.py`), и ручных полей у тем нет (карточка RN-11).
    Правило 23 распространяется на заходы: у каждого обязан быть вопрос с
    выбором из трёх вариантов с разбором, как у темы-уязвимости.
    """
    data = vc.load_yaml(ROOT / "thresholds.yaml") or {}
    out: dict[str, list[str]] = {}
    for concept in data.get("concepts") or []:
        for a in concept.get("approaches") or []:
            out.setdefault(str(a["topic"]), []).append(str(concept["id"]))
    return out


def questions(raw: list[str], split: int) -> list[str]:
    """Вопросы блока: нумерованный пункт вместе со строками-продолжениями.

    Продолжение — всё до следующего пункта или до `<details>`: вопрос с
    фрагментом кода или вариантами занимает несколько строк.
    """
    out: list[list[str]] = []
    for line in raw[:split]:
        if vc.LIST_NUM_RE.match(line):
            out.append([line])
        elif out:
            out[-1].append(line)
    return ["\n".join(q) for q in out]


def topic_stats(page: vc.Page, ctx: vc.Ctx,
                approaches: dict[str, list[str]] | None = None) -> dict | None:
    """Метрики одной темы; None, если блока самопроверки нет (уровень L3)."""
    skeleton = ctx.skeleton_of(page)
    # Блок ищется по ключу, а не по номеру: номер зависит от скелета, а в
    # теме-статье (переходный режим, решение оператора 2026-10-02) заголовков
    # с номерами нет вовсе — там «Проверь себя» распознаётся по имени.
    block = vc.block_by_key(page, ctx, skeleton, "selfcheck")
    if block is None:
        return None
    raw = page.lines[block.start:block.end]
    split = next((i for i, line in enumerate(raw)
                  if line.startswith("<details")), len(raw))
    qs = questions(raw, split)

    # Фрагменты: ограждённые блоки внутри вопросов. «Новый для темы» — текст
    # фрагмента не встречается выше блока самопроверки.
    above = "\n".join(page.lines[:block.start])
    fences = [f.strip() for q in qs for f in FENCE_RE.findall(q)]
    new_fences = [f for f in fences if f and f not in above]

    # Вопросы с выбором: три-четыре строки-варианта в тексте вопроса.
    choices = []
    for q in qs:
        letters = [m.group("letter") for line in q.split("\n")
                   if (m := VARIANT_RE.match(line))]
        if len(letters) >= 3:
            choices.append({"variants": len(letters),
                            "catchall": any(CATCHALL_RE.match(line)
                                            for line in q.split("\n"))})
    # Разбор вариантов: `<details>` со «Разбор» в summary и строкой на вариант.
    answers = "\n".join(raw[split:])
    reviews = 0
    for body in DETAILS_RE.findall(answers):
        m = SUMMARY_RE.search(body)
        if m and "азбор" in m.group(1):
            reviews = max(reviews, len([ln for ln in body.split("\n")
                                        if VARIANT_RE.match(ln)]))

    pos = ctx.route_pos.get(page.id, (99, 10 ** 9))
    far = near = 0
    for q in qs:
        for ref in vc.RETURN_RE.findall(q):
            target = ctx.route_pos.get(ref)
            if target is not None:
                far += target[0] != pos[0]
                near += target[0] == pos[0]
    return {
        "id": page.id,
        "stage": pos[0],
        "depth": page.depth,
        "skeleton": skeleton,
        "approach": (approaches or {}).get(page.id) or [],
        "questions": len(qs),
        "fragments": len(fences),
        "new_fragments": len(new_fences),
        "inline": sum(1 for q in qs if INLINE_RE.search(q)),
        "why": sum(1 for q in qs if WHY_RE.search(q)),
        "predict": sum(1 for q in qs if PREDICT_RE.search(q)),
        "doc_says": sum(1 for q in qs if DOC_SAYS_RE.search(q)),
        "choices": choices,
        "reviews": reviews,
        "far": far,
        "near": near,
    }


def failures(st: dict) -> list[str]:
    """Нарушения машинно-проверяемой части правил 23, 24 и 35 — для --verdict."""
    out = []
    if st["fragments"] < 2 or not st["new_fragments"]:
        out.append(f"фрагментов в вопросах {st['fragments']}"
                   f" (новых {st['new_fragments']}) при норме 2, один новый")
    need_choice = st["skeleton"] == "уязвимость" or bool(st["approach"])
    if need_choice and not st["choices"]:
        if st["skeleton"] == "уязвимость":
            out.append("тема-уязвимость без вопроса с выбором из трёх вариантов")
        else:
            out.append("тема-заход пороговой концепции "
                       f"({', '.join(st['approach'])}) без вопроса с выбором "
                       "из трёх вариантов (thresholds.yaml)")
    for ch in st["choices"]:
        if not 3 <= ch["variants"] <= 4:
            out.append(f"вариантов {ch['variants']} при норме 3 (четвёртый — "
                       "при четвёртом заблуждении)")
        if ch["catchall"]:
            out.append("вариант «всё / ничего из перечисленного»")
        if st["reviews"] < ch["variants"]:
            out.append(f"разборов {st['reviews']} при {ch['variants']} вариантах: "
                       "каждый вариант разбирается под `<details>`")
    if st["stage"] >= 2 and st["depth"] in ("L1", "L2") and not st["far"]:
        out.append("нет возврата на другой этап (правило 35, темы со этапа 2)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*",
                    help="темы; по умолчанию весь content/**")
    ap.add_argument("--full", action="store_true",
                    help="строка на каждую тему, а не только сводка")
    ap.add_argument("--verdict", action="store_true",
                        help="код возврата 1 при нарушении машинной части "
                             "правил 23, 24, 35 — режим гейта: с этим флагом "
                             "скрипт стоит в реестре tools/check.py")
    args = ap.parse_args()

    ctx = vc.Ctx()
    approaches = approach_topics()
    wanted = {str(Path(p)) for p in args.paths}
    rows = []
    for path in mdtext.topics():
        if wanted and str(path) not in wanted:
            continue
        st = topic_stats(vc.read_page(path), ctx, approaches)
        if st is not None:
            rows.append(st)

    total_q = sum(r["questions"] for r in rows)
    frag_q = sum(r["fragments"] for r in rows)
    vuln = [r for r in rows if r["skeleton"] == "уязвимость"]
    appr = [r for r in rows if r["approach"]]
    late = [r for r in rows if r["stage"] >= 2 and r["depth"] in ("L1", "L2")]

    print(f"тем с блоком «Проверь себя»: {len(rows)}, вопросов: {total_q}")
    print("правило 24 — понимание, не воспроизведение:")
    print(f"  вопросов с фрагментом кода/HTTP/конфига: {frag_q}; "
          f"тем с нормой «2 фрагмента, один новый»: "
          f"{sum(1 for r in rows if r['fragments'] >= 2 and r['new_fragments'])}"
          f" из {len(rows)}")
    print(f"  тем с вопросом «почему»: {sum(1 for r in rows if r['why'])}"
          f" из {len(rows)}; с вопросом-предсказанием: "
          f"{sum(1 for r in rows if r['predict'])} из {len(rows)} (эвристики)")
    print(f"  вопросов «что называет/предписывает документ»: "
          f"{sum(r['doc_says'] for r in rows)} (эвристика, законны, только "
          "если документ — предмет темы)")
    print("правило 23 — вопрос с выбором из трёх вариантов:")
    print(f"  тем-уязвимостей с таким вопросом: "
          f"{sum(1 for r in vuln if r['choices'])} из {len(vuln)}; "
          f"тем-заходов пороговых концепций: "
          f"{sum(1 for r in appr if r['choices'])} из {len(appr)} "
          "(разметка П1–П6 — thresholds.yaml)")
    print("правило 35 — дальний возврат (темы L1–L2 со этапа 2):")
    print(f"  тем с возвратом на другой этап: {sum(1 for r in late if r['far'])}"
          f" из {len(late)}")

    bad = [(r, failures(r)) for r in rows]
    bad = [(r, ff) for r, ff in bad if ff]
    # Тема-заход, не попавшая в отчёт (нет страницы или блока самопроверки),
    # не должна проходить гейт молча: проверить вопрос с выбором у неё
    # невозможно, а правило 23 её обязывает. При запуске на части корпуса
    # (`paths`) пропуски ожидаемы и не считаются.
    missing = sorted(set(approaches) - {r["id"] for r in rows}) \
        if not wanted else []
    if args.full:
        print("\nпо темам: фрагменты(новые) · выбор · дальних возвратов")
        for r in rows:
            ch = ";".join(str(c["variants"]) for c in r["choices"]) or "—"
            print(f"  {r['id']:<38} {r['fragments']}({r['new_fragments']})"
                  f" · {ch} · {r['far']}")
    if bad:
        print(f"\nмашинная часть правил не выполнена в {len(bad)} темах из "
              f"{len(rows)}" + ("" if args.full else " — список: `--full`"))
        if args.full:
            for r, ff in bad:
                for f in ff:
                    print(f"  {r['id']}: {f}")
    if missing:
        print(f"\nтемы-заходы из thresholds.yaml без блока «Проверь себя» "
              f"в отчёте ({len(missing)}): " + ", ".join(missing))

    if not args.verdict:
        print("\nотчёт без вердикта; в гейте скрипт стоит с `--verdict` "
              "(реестр tools/check.py)")
        return 0
    if bad or missing:
        print(f"\n--verdict: не пройдено, {len(bad) + len(missing)} тем")
        return 1
    print("\n--verdict: пройдено")
    return 0


if __name__ == "__main__":
    sys.exit(main())
