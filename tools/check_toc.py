#!/usr/bin/env python3
"""Машинная сверка оглавления этапа 3 с планом и корпусом.

Проверяет до написания единого знака темы то, что не проверяет никто другой:
состав оглавления против `topics.yaml`, словари, предпосылки (разрешение,
отсутствие циклов, согласованность порядка), инвариант «L3 не может быть
предпосылкой», длину заголовка, совпадение с уже написанным.

Происхождение: проверка жила в каталогах миссий оглавлений в трёх
расходящихся копиях (заявки З-04 этапов 1–2, З-05 этапа 3); перенесена в
обвязку в самой полной версии — этапа 3, она единственная умеет два скелета.

    python tools/check_toc.py

Вход — `.smgr/appsec-stage3-toc/toc.yaml`: состояние миссии оглавления, в
репозиторий не входит (`.smgr/` в `.gitignore`). Без него проверка честно
печатает ПРОПУЩЕНО и завершается нулём. Печатает отчёт и список нарушений;
код возврата 1, если нарушения есть. Выведенный порядок чтения записывает
рядом со входом, в `order.yaml`.
"""

import heapq
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from paths import CONTENT_DIR, ROOT, SMGR_DIR, TAXONOMY_YAML, TOPICS_YAML
from plan_parse import SKIP_MARK

TOC = SMGR_DIR / "appsec-stage3-toc" / "toc.yaml"
STAGE = 3
TITLE_MAX = 60          # SCHEMA.md § 3, правило C-FM-TITLE-LEN
PREREQ_MAX = 4          # свод 9.1: только прямые, не больше четырёх
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TOOL_VALUES = {"free", "installed", "limited", "paid", "none"}

errors, warnings = [], []


def err(rule, msg):
    errors.append(f"{rule}: {msg}")


def warn(rule, msg):
    warnings.append(f"{rule}: {msg}")


# --- входные данные ---------------------------------------------------------

if not TOC.is_file():
    print(f"{SKIP_MARK}: нет {TOC.relative_to(ROOT)} — это состояние миссии "
          "оглавления, в репозиторий оно не входит")
    sys.exit(0)

raw = yaml.safe_load(TOC.read_text(encoding="utf-8"))
toc, reorder = raw["topics"], raw.get("reorder") or []
taxonomy = yaml.safe_load(TAXONOMY_YAML.read_text(encoding="utf-8"))
topics_yaml = yaml.safe_load(TOPICS_YAML.read_text(encoding="utf-8"))

# план -> плоский список plan_id этапа 3 в порядке плана, и подраздел каждой
# темы
plan_ids, plan_titles, plan_sub = [], {}, {}
sub_titles = {}
for stage in topics_yaml["stages"]:
    if stage["num"] != STAGE:
        continue
    for sub in stage["subsections"]:
        sub_titles[sub["num"]] = sub["title"]
        for t in sub["topics"]:
            plan_ids.append(t["id"])
            plan_titles[t["id"]] = t["title"]
            plan_sub[t["id"]] = sub["num"]
plan_pos = {pid: i + 1 for i, pid in enumerate(plan_ids)}

# уже написанное: frontmatter всех тем в content/ (этапы 0, 1, 2)
stage_num = {s["slug"]: s["num"] for s in taxonomy["stages"]}
written = {}
for md in sorted(CONTENT_DIR.glob("stage-*/*.md")):
    fm = yaml.safe_load(md.read_text(encoding="utf-8").split("---")[1])
    fm["_stage_num"] = stage_num[fm["stage"]]
    written[fm["id"]] = fm
earlier_ids = {i for i, fm in written.items() if fm["_stage_num"] < STAGE}
stage3_written = {i: fm for i, fm in written.items()
                  if fm["_stage_num"] == STAGE}
if not earlier_ids:
    err("T-SELFTEST", "не прочитан ни один frontmatter этапов 0–2 — "
                      "проверка предпосылок бессмысленна")

# состав обязательных блоков: свой у каждого скелета (свод 3.1, 4.2)
req_blocks = {}
block_title = {}
for sk_name, sk in taxonomy["skeletons"].items():
    for b in sk["blocks"]:
        block_title[(sk_name, b["num"])] = b["title"]
        for d in b["required"]:
            req_blocks.setdefault((sk_name, d), set()).add(b["num"])

# --- 1. состав --------------------------------------------------------------

toc_ids = [t["plan_id"] for t in toc]
if len(set(toc_ids)) != len(toc_ids):
    dup = [i for i in set(toc_ids) if toc_ids.count(i) > 1]
    err("T-COMP-DUP", f"plan_id повторяется: {sorted(dup)}")
missing = [p for p in plan_ids if p not in set(toc_ids)]
extra = [p for p in toc_ids if p not in set(plan_ids)]
if missing:
    err("T-COMP-MISS", f"темы плана без строки оглавления: {missing}")
if extra:
    err("T-COMP-EXTRA", f"строки оглавления без темы в плане: {extra}")

# --- 2. слаги, заголовки, словари ------------------------------------------

by_slug = {}
title_cut = {}
for t in toc:
    pid, slug = t["plan_id"], t["slug"]
    if not SLUG_RE.match(slug):
        err("T-SLUG-FORM", f"{pid}: слаг «{slug}» не kebab-case")
    if slug in by_slug:
        err("T-SLUG-DUP", f"слаг «{slug}» у {by_slug[slug]} и {pid}")
    by_slug[slug] = pid
    # Слаг занят темой ДРУГОГО этапа — столкновение адресов. Тема своего
    # этапа с тем же слагом — это не конфликт, а уже написанная строка
    # оглавления; её согласованность проверяет раздел 5.
    if slug in written and written[slug]["_stage_num"] != STAGE:
        err("T-SLUG-CLASH",
            f"{pid}: слаг «{slug}» занят написанной темой этапа "
            f"{written[slug]['_stage_num']}")
    n = len(t["title"])
    if n > TITLE_MAX:
        err("T-TITLE-LEN", f"{pid}: заголовок {n} знаков > {TITLE_MAX}")
    title_cut[pid] = (len(plan_titles.get(pid, "")), n)
    if t["depth"] not in taxonomy["depths"]:
        err("T-VOCAB-DEPTH", f"{pid}: уровень «{t['depth']}» вне словаря")
    if t["mode"] not in taxonomy["modes"]:
        err("T-VOCAB-MODE", f"{pid}: режим «{t['mode']}» вне словаря")
    if t.get("skeleton") not in taxonomy["skeletons"]:
        err("T-VOCAB-SKEL",
            f"{pid}: скелет «{t.get('skeleton')}» вне словаря "
            f"{sorted(taxonomy['skeletons'])}")
    if t.get("tool") not in TOOL_VALUES:
        err("T-TOOL",
            f"{pid}: доступность инструмента «{t.get('tool')}» вне "
            f"{sorted(TOOL_VALUES)}")
    if t.get("tool") in ("paid", "limited") and not t.get("tool_note"):
        err("T-TOOL-NOTE",
            f"{pid}: доступность «{t['tool']}» объявлена без оговорки "
            "в tool_note")
    if t.get("tool") not in ("paid", "limited") and t.get("tool_note"):
        err("T-TOOL-NOTE",
            f"{pid}: оговорка tool_note при доступности "
            f"«{t.get('tool')}» — оговаривать нечего")
    if not t.get("why"):
        err("T-WHY-EMPTY", f"{pid}: не записана причина уровня")
    # no_referent — блоки НАЗНАЧЕННОГО скелета, у которых на этой теме нет
    # предмета. Блок, который уровню и так не положен, в списке — мусор.
    here = req_blocks.get((t.get("skeleton"), t["depth"]), set())
    for b in t.get("no_referent") or []:
        if b not in here:
            err("T-NOREF-VOCAB",
                f"{pid}: блок {b} у скелета «{t.get('skeleton')}» "
                f"на уровне {t['depth']} и так не обязателен")
    if t.get("crit") not in (1, 2, 3, 4, 5):
        err("T-CRIT", f"{pid}: критерий 3.2 не указан или вне 1..5")
    if t.get("crit") == 5 and t["depth"] != "L3":
        err("T-CRIT-L3",
            f"{pid}: критерий 5 по своду даёт L3, а стоит {t['depth']}")
    if t["depth"] == "L3" and t.get("crit") != 5:
        err("T-CRIT-L3",
            f"{pid}: уровень L3 при критерии {t.get('crit')}; "
            "по 3.2 L3 даёт только пункт 5")
    # поле fixes_in законно только у темы-инструмента (свод 4.2,
    # C-FM-SKELETON). В оглавлении оно не назначается, но скелет назначается —
    # и он определяет, обязано ли поле появиться при письме. Проверяем
    # связность заранее.
    if t.get("skeleton") == "уязвимость" and t.get("fixes_in") is not None:
        err("T-SKEL-FIX", f"{pid}: fixes_in у темы со скелетом уязвимости")

slug_of = {t["plan_id"]: t["slug"] for t in toc}
depth_of = {t["slug"]: t["depth"] for t in toc}

# --- 3. предпосылки ---------------------------------------------------------

known = set(by_slug) | earlier_ids
prereqs = {}
for t in toc:
    pid, slug = t["plan_id"], t["slug"]
    pre = t.get("prerequisites") or []
    prereqs[slug] = pre
    if len(pre) > PREREQ_MAX:
        err("T-PRE-MANY", f"{pid}: {len(pre)} предпосылок > {PREREQ_MAX}")
    if len(set(pre)) != len(pre):
        err("T-PRE-DUP", f"{pid}: предпосылка повторяется")
    for p in pre:
        if p == slug:
            err("T-PRE-SELF", f"{pid}: тема указана предпосылкой самой себя")
        elif p not in known:
            err("T-PRE-UNKNOWN",
                f"{pid}: предпосылка «{p}» не существует ни на одном этапе")

# инвариант, выведенный из 3.2 п.4 и решения 3 миссии appsec-stage0-close:
# тема, на которую опирается другая тема, не может быть уровня «узнать».
carried = {}
for slug, pre in prereqs.items():
    for p in pre:
        carried.setdefault(p, []).append(slug)
for p, deps in sorted(carried.items()):
    if depth_of.get(p) == "L3":
        err("T-L3-CARRIES", f"L3-тема «{p}» несёт на себе {sorted(deps)}")
    if p in earlier_ids and written[p]["depth"] == "L3":
        err("T-L3-CARRIES-EARLY",
            f"L3-тема этапа {written[p]['_stage_num']} «{p}» "
            f"несёт на себе {sorted(deps)}")

# --- 4. циклы и линейный порядок -------------------------------------------

stage3_pre = {s: [p for p in pre if p in by_slug]
              for s, pre in prereqs.items()}

order_slugs = [slug_of[p] for p in plan_ids]
for mv in reorder:
    s_, after = mv["slug"], mv["after"]
    if s_ not in by_slug:
        err("T-MOVE-UNKNOWN", f"перенос: темы «{s_}» нет в оглавлении")
        continue
    if after not in by_slug:
        err("T-MOVE-UNKNOWN",
            f"перенос «{s_}»: якоря «{after}» нет в оглавлении")
        continue
    if not mv.get("why"):
        err("T-MOVE-WHY", f"перенос «{s_}» без причины")
    order_slugs.remove(s_)
    order_slugs.insert(order_slugs.index(after) + 1, s_)

indeg = {s: len(v) for s, v in stage3_pre.items()}
dependents = {s: [] for s in stage3_pre}
for s, pre in stage3_pre.items():
    for p in pre:
        dependents[p].append(s)
heap = [(order_slugs.index(s), s) for s, d in indeg.items() if d == 0]
heapq.heapify(heap)
laid = []
while heap:
    _, s = heapq.heappop(heap)
    laid.append(s)
    for d in dependents[s]:
        indeg[d] -= 1
        if indeg[d] == 0:
            heapq.heappush(heap, (order_slugs.index(d), d))
if len(laid) != len(stage3_pre):
    err("T-CYCLE", f"цикл предпосылок: {sorted(set(stage3_pre) - set(laid))}")

pos = {s: i + 1 for i, s in enumerate(order_slugs)}
for s, pre in stage3_pre.items():
    for p in pre:
        if pos[p] > pos[s]:
            err("T-ORDER",
                f"«{s}» (место {pos[s]}) стоит раньше своей предпосылки "
                f"«{p}» (место {pos[p]})")

# order этапа 3 продолжает нумерацию: у каждого этапа своя, шаг тот же.
order_val = {s: pos[s] * 10 for s in order_slugs}
seen = set()
for s, o in order_val.items():
    if o % 10 or o in seen:
        err("T-ORDER-FORM", f"«{s}»: order {o} не кратен 10 либо не уникален")
    seen.add(o)

# --- 5. совпадение с уже написанным ----------------------------------------

for wid, fm in stage3_written.items():
    row = next((t for t in toc if t["slug"] == wid), None)
    if row is None:
        err("T-WRITTEN-MISS",
            f"написанная тема «{wid}» отсутствует в оглавлении")
        continue
    for field in ("depth", "mode", "plan_id"):
        if fm[field] != row[field]:
            err(f"T-WRITTEN-{field.upper()}",
                f"{wid}: в файле {fm[field]}, в оглавлении {row[field]}")
    if fm.get("skeleton", taxonomy["default_skeleton"]) != row["skeleton"]:
        err("T-WRITTEN-SKELETON",
            f"{wid}: в файле скелет "
            f"{fm.get('skeleton', taxonomy['default_skeleton'])}, "
            f"в оглавлении {row['skeleton']}")

# --- 6. разрывы в словарях (заявки, не ошибки оглавления) ------------------

cat_subs = {v["sub"] for v in taxonomy["code_categories"].values()}
subs_needed = sorted({plan_sub[t["plan_id"]] for t in toc})
subs_missing = [s for s in subs_needed if s not in cat_subs]

# теги: собраны по предмету восьми тем; в словаре ищется каждый
tag_probe = ["ci-cd"]
tags_reused = ["tooling", "architecture", "triage", "sast", "injection",
               "supply-chain", "access-control", "crypto", "secrets", "auth"]
tags_missing = [t for t in tag_probe if t not in taxonomy["tags"]]
reused_missing = [t for t in tags_reused if t not in taxonomy["tags"]]
if reused_missing:
    err("T-TAG-REUSE",
        f"тег, объявленный переиспользуемым, из словаря пропал: "
        f"{reused_missing}")

# --- 7. числа ---------------------------------------------------------------

by_depth, by_mode, by_crit, by_tool, by_skel = {}, {}, {}, {}, {}
for t in toc:
    by_depth[t["depth"]] = by_depth.get(t["depth"], 0) + 1
    by_mode[t["mode"]] = by_mode.get(t["mode"], 0) + 1
    by_crit[t["crit"]] = by_crit.get(t["crit"], 0) + 1
    by_tool[t["tool"]] = by_tool.get(t["tool"], 0) + 1
    by_skel[t["skeleton"]] = by_skel.get(t["skeleton"], 0) + 1

forward = []
for s, pre in stage3_pre.items():
    for p in pre:
        if plan_pos[by_slug[p]] > plan_pos[by_slug[s]]:
            forward.append((by_slug[s], s, p))
moved = [s for s in order_slugs if pos[s] != plan_pos[by_slug[s]]]
early_used = [p for pre in prereqs.values() for p in pre if p in earlier_ids]
by_early_stage = {}
for p in early_used:
    n = written[p]["_stage_num"]
    by_early_stage.setdefault(n, []).append(p)
no_deps = sorted(s for s in by_slug.values() if slug_of[s] not in carried)

# часы: L1/L2/L3 выведены из таблицы 3.4 свода (три строки на 250 тем при
# L3 = 2 ч дают систему, решаемую однозначно; все три строки сходятся точно)
HOURS = {"L1": 46 / 3, "L2": 38 / 3, "L3": 2.0}
cost = sum(HOURS[t["depth"]] for t in toc)
ref = (0.15 * len(toc) * HOURS["L1"] + 0.45 * len(toc) * HOURS["L2"]
       + 0.40 * len(toc) * HOURS["L3"])

print(f"тем в плане (этап {STAGE}): {len(plan_ids)} "
      f"в {len(sub_titles)} подразделах")
print(f"строк в оглавлении:        {len(toc)}")
print("уровни:  "
      + ", ".join(f"{k} {by_depth.get(k, 0)}" for k in ("L1", "L2", "L3")))
pct = {k: 100.0 * by_depth.get(k, 0) / len(toc) for k in ("L1", "L2", "L3")}
print("доли, %: "
      + ", ".join(f"{k} {pct[k]:.0f}" for k in ("L1", "L2", "L3")))
print("режимы:  "
      + ", ".join(f"{k} {v}" for k, v in
                  sorted(by_mode.items(), key=lambda x: -x[1])))
print("скелеты: "
      + ", ".join(f"{k} {v}" for k, v in
                  sorted(by_skel.items(), key=lambda x: -x[1])))
print("критерий 3.2: "
      + ", ".join(f"п.{k} — {by_crit[k]}" for k in sorted(by_crit)))
print("инструменты: "
      + ", ".join(f"{k} {v}" for k, v in sorted(by_tool.items())))
n_pre = sum(len(v) for v in prereqs.values())
n_pre_out = sum(1 for pre in prereqs.values() for p in pre
                if p in earlier_ids)
n_pre_in = sum(len(v) for v in stage3_pre.values())
print(f"предпосылок всего: {n_pre}; наружу (этапы 0–2): {n_pre_out}; "
      f"внутри этапа 3: {n_pre_in}")
for n in sorted(by_early_stage):
    print(f"    на этап {n}: {len(by_early_stage[n])} ссылок, "
          f"{len(set(by_early_stage[n]))} тем — "
          f"{sorted(set(by_early_stage[n]))}")
print("тем без предпосылок внутри этапа: "
      f"{sum(1 for v in stage3_pre.values() if not v)}")
print(f"тем, на которые никто не опирается: {len(no_deps)}")
print("опережающих предпосылок (предпосылка позже по плану): "
      f"{len(forward)}")
for pid, s, p in sorted(forward, key=lambda x: plan_pos[x[0]]):
    print(f"    {pid} {s} <- {p} ({by_slug[p]}, "
          f"план {plan_pos[by_slug[p]]})")
print(f"переносов в оглавлении: {len(reorder)}")
print("тем, чьё место в чтении сдвинулось относительно плана: "
      f"{len(moved)}")
for s in moved:
    print(f"    {by_slug[s]} {s}: план {plan_pos[by_slug[s]]} -> "
          f"чтение {pos[s]} (order {order_val[s]})")
print("несущие темы (сколько тем этапа 3 опирается):")
for p, deps in sorted(carried.items(), key=lambda x: (-len(x[1]), x[0])):
    where = (depth_of.get(p)
             or f"этап {written[p]['_stage_num']}, {written[p]['depth']}")
    print(f"    {p:<26} {len(deps)}  {where}")
print(f"цена этапа: {cost:.0f} ч (L1 {HOURS['L1']:.2f} ч, "
      f"L2 {HOURS['L2']:.2f} ч, L3 2 ч)")
print(f"    для сравнения, средняя строка 3.4 (15/45/40) на {len(toc)} "
      f"темах: {ref:.0f} ч")
print("заголовки: план -> оглавление (знаков)")
for pid in plan_ids:
    a, b = title_cut[pid]
    mark = " ← укорочен" if b < a else ""
    print(f"    {pid}: {a} -> {b}{mark}")
print(f"    длиннее {TITLE_MAX} знаков в плане: "
      f"{sum(1 for pid in plan_ids if title_cut[pid][0] > TITLE_MAX)} "
      f"из {len(plan_ids)}")

# версионность выводится из заголовка темы в плане обучения, а не объявляется:
# тема, названная именем продукта или синтаксисом конкретной системы,
# протухает вместе с ними. Список короче, чем на этапе 2, и это само по себе
# замер.
PRODUCTS = ["GitHub Actions", "GitLab CI", "Vault", "pre-commit", "workflow",
            "pull_request_target", "сторонним action"]
versioned = {}
for t in toc:
    hits = [p for p in PRODUCTS
            if p.lower() in plan_titles[t["plan_id"]].lower()]
    versioned[t["slug"]] = hits
nver = sum(1 for v in versioned.values() if v)
print(f"тем, названных в плане именем продукта или синтаксисом системы: "
      f"{nver} из {len(toc)}")
for s in order_slugs:
    if versioned[s]:
        print(f"    {s}: {', '.join(versioned[s])}")

noref_by_block, noref_topics = {}, []
for t in toc:
    nr = t.get("no_referent") or []
    if nr:
        noref_topics.append(t["slug"])
    for b in nr:
        noref_by_block.setdefault((t["skeleton"], b), []).append(t["slug"])
print(f"тем, у которых хотя бы один обязательный блок назначенного скелета "
      f"без предмета: {len(noref_topics)} из {len(toc)}")
for (sk, b) in sorted(noref_by_block):
    print(f"    скелет «{sk}», блок {b} «{block_title[(sk, b)]}»: "
          f"{len(noref_by_block[(sk, b)])} тем")
print("подразделы этапа 3 без категории в code_categories: "
      f"{len(subs_missing)} — {subs_missing}")
print(f"тегов предмета этапа 3, которых нет в словаре: {len(tags_missing)} "
      f"— {tags_missing}")
print(f"тегов, взятых из уже заведённых: {len(tags_reused)} — {tags_reused}")

print()
if warnings:
    print(f"ПРЕДУПРЕЖДЕНИЙ: {len(warnings)}")
    for w in warnings:
        print("  " + w)
if errors:
    print(f"НАРУШЕНИЙ: {len(errors)}")
    for e in errors:
        print("  " + e)
    sys.exit(1)
print("НАРУШЕНИЙ НЕТ")

out = TOC.parent / "order.yaml"
out.write_text(yaml.safe_dump(
    {"order": [{"pos": pos[s], "order": order_val[s], "slug": s,
                "plan_id": by_slug[s], "plan_pos": plan_pos[by_slug[s]],
                "sub": plan_sub[by_slug[s]]}
               for s in order_slugs]},
    allow_unicode=True, sort_keys=False), encoding="utf-8")
print(f"порядок чтения записан: {out.relative_to(ROOT)}")
