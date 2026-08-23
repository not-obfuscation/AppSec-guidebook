#!/usr/bin/env python3
"""Проверка проверок: каждое правило ловит своё и молчит на законном.

    python tools/lint_selftest.py            # прогон, одна строка на утверждение
    python tools/lint_selftest.py --quiet    # только провалы и итог
    python tools/lint_selftest.py --keep     # оставить фикстуры на диске

Линтер, который молчит, снаружи неотличим от линтера, который сломан: и там и
там пусто. Поэтому у каждого правила из `STYLE.md` § 2 и `SCHEMA.md` § 8
здесь есть фикстура,
на которой оно обязано сработать, а у решений, принятых при отладке правил, —
фикстура, на которой оно обязано молчать. Второе важнее первого: почти все
правки этой обвязки были не «правило не ловит», а «правило ловит лишнее».

Отдельное условие приёмки — § 4: **ни одно правило не помечает хеджирование**.
Список модальных слов свода прогоняется как текст через все инструменты сразу,
и любое срабатывание на нём — дефект обвязки.

Фикстуры пишутся во временный каталог и прогоняются теми же функциями, что
`tools/check.py`: селф-тест проверяет не только правила, но и приведение
идентификаторов и уровней к общему виду. Проверки уровня данных (`G-GLOSS`,
`G-SYNSET`, `G-UNUSED`) вызываются напрямую на синтетическом глоссарии.

Выход 1, если хоть одно утверждение не сошлось.
"""

import argparse
import copy
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check
import glossary_lint as gl
import lint_style as ls  # noqa: F401  — импорт держит зависимость явной
import mdtext
import linkcheck as lc
import validate_content as vc
import wordcount as wcnt

CATCH, SILENT = "ловит", "молчит"
ANY = "*"


@dataclass
class Case:
    """Одно утверждение о правиле."""

    name: str
    rule: str
    mode: str
    body: str
    level: str = ""
    count: int = 0  # 0 — «хотя бы одно»
    page_id: str = ""
    prereq: tuple = ()
    why: str = ""


def fence(lines, lang="text") -> str:
    return "```" + lang + "\n" + "\n".join(lines) + "\n```"


def words(n: int, word: str = "слово") -> str:
    return " ".join([word] * n)


# ── фикстуры ─────────────────────────────────────────────────────────────────

HEDGING = """Обычно сервер отвечает кодом 200. Как правило, срок жизни задан явно.
При необходимости поле добавляется на границе. Допускается пустое значение.
Могут быть и другие сочетания. В большинстве случаев ответ кешируется.
Зачастую граница проходит по домену. Как минимум одна проверка обязательна.
Скорее всего, запрос уйдёт повторно. По умолчанию атрибут не выставлен."""

CASES = [
    # --- Vale: 6.1, 6.3, 6.4, 6.5 --------------------------------------------
    Case("обращение на «ты»", "L-ADDRESS", CATCH,
         "Дальше ты открываешь панель и смотришь заголовок."),
    Case("канцелярит", "L-CLERICAL", CATCH,
         "Заголовок является обязательным для запроса."),
    Case("«данные» под вопросом", "L-CLERICAL2", CATCH,
         "Эти данные приходят из формы.", level="warning"),
    Case("обесценивающее слово", "L-BANNED", CATCH,
         "Такой запрос просто уходит на сервер."),
    Case("оценка без факта", "L-EVAL", CATCH,
         "Схема удобная для разбора."),
    Case("вводный штамп", "L-FILLER", CATCH,
         "Стоит отметить, что заголовок обязателен."),
    Case("навигация словом", "L-NAV", CATCH,
         "Разбор лежит [здесь](#razbor)."),
    Case("время без даты", "L-TIMELESS", CATCH,
         "Сейчас браузер отклоняет такой ответ.", level="warning"),
    Case("восклицательный знак", "L-EMOJI", CATCH,
         "Ответ пришёл! Разбор дальше."),
    Case("склонение латиницы", "L-LATIN", CATCH,
         "Подпись JWT'ом не проверяется."),
    Case("прямые кавычки", "L-QUOTES", CATCH,
         'Заголовок "Host" читается сервером.'),
    Case("дефис вместо тире", "L-DASH", CATCH,
         "Заголовок - это имя и значение."),
    Case("диапазон через дефис", "L-RANGE", CATCH,
         "Срок действия 2020-2024 указан в реестре."),
    Case("процент без пробела", "L-PERCENT", CATCH,
         "Доля 20% запросов уходит мимо кеша."),
    Case("неразрывный пробел", "L-NBSP", CATCH,
         "Ответ приходит за 30 мин после запроса.", level="warning"),
    Case("«е» вместо «ё»", "L-YO", CATCH,
         "Сервер дает ответ на запрос."),

    # --- § 4: хеджирование не помечает никто ---------------------------------
    Case("хеджирование не помечено", ANY, SILENT, HEDGING,
         why="STYLE.md § 4: срабатывание здесь — дефект обвязки, а не текста"),

    # --- свои правила: 7.1 и 6.4 ---------------------------------------------
    Case("широкая строка листинга", "S-CODE-WIDTH", CATCH,
         fence(["x" * 90]), level="error"),
    Case("строка ровно 76 символов", "S-CODE-WIDTH", SILENT,
         fence(["x" * 76]),
         why="76 — предел из 7.1 п. 3, а не первое запрещённое значение"),
    Case("листинг длиннее 40 строк", "S-CODE-LEN", CATCH,
         fence([f"строка {i}" for i in range(45)]), level="error"),
    Case("листинг длиннее 25 строк", "S-CODE-LEN", CATCH,
         fence([f"строка {i}" for i in range(30)]), level="warning"),
    Case("знак препинания в коде", "S-CODE-PUNCT", CATCH,
         "Заголовок `Host.` в запросе.", level="warning"),
    Case("схема URI в коде", "S-CODE-PUNCT", SILENT,
         "Значения `data:` и `javascript:` в атрибуте, разделитель `.` в имени.",
         why="двоеточие — часть схемы, а не приклеенная пунктуация"),
    Case("номера списка вразнобой", "S-LIST-ORDER", CATCH,
         "1. Первый пункт.\n3. Третий пункт.", level="error"),
    Case("список с четвёртого пункта", "S-LIST-ORDER", SILENT,
         "4. Четвёртый пункт.\n5. Пятый пункт.",
         why="выноски к листингу нумеруются внутри листинга — 7.4 п. 32"),
    Case("пунктуация списка вразнобой", "S-LIST-MIX", CATCH,
         "- Первый пункт;\n- второй пункт.\n- Третий пункт;", level="warning"),
    Case("список вопросов", "S-LIST-MIX", SILENT,
         "- Что отправит браузер?\n- Что вернёт сервер?\n- Где граница доверия.",
         why="вопросительный знак — та же точка: блок 12 канона"),
    Case("длинное предложение", "S-SENT-LONG", CATCH,
         "Браузер " + words(30) + " дальше.", level="warning"),
    Case("сокращение не делит предложение", "S-SENT-LONG", CATCH, count=1,
         body="Браузер " + words(14) + ", т. д. и " + words(14) + " дальше.",
         why="точка в «т. д.» не начинает предложение: иначе два коротких "
             "куска вместо одного длинного, и правило промолчит"),
    Case("длинный абзац", "S-PARA-LONG", CATCH,
         ". ".join("Сервер " + words(18) for _ in range(6)) + ".",
         level="warning"),
    Case("заголовок четвёртого уровня", "S-HEAD-DEPTH", CATCH,
         "#### Четвёртый уровень\n\nАбзац под ним."),

    # --- markdownlint: как настроен конфиг -----------------------------------
    Case("пробел в конце строки", "MD009", CATCH, "Строка с пробелом в конце. "),
    Case("листинг без языка", "MD040", CATCH, "```\ntext\n```"),
    Case("пропуск уровня заголовка", "MD001", CATCH,
         "#### Сразу четвёртый\n\nАбзац под ним."),
    Case("длинная строка прозы", "MD013", SILENT,
         "Сервер " + words(20, "ответ") + " дальше.",
         why="норма длины строки сводом не задана — 6.7"),
    Case("написание термина", "MD044", SILENT,
         "Схема описана на graphql.org в разделе про типы.",
         why="за написания отвечает G-CANON, он знает про домены и код"),
    Case("нумерация с четвёртого", "MD029", SILENT,
         "4. Четвёртый пункт.\n5. Пятый пункт.",
         why="то же решение, что и у S-LIST-ORDER"),
    Case("абзац из выделения", "MD036", SILENT, "**Описание схемы.**",
         why="служебный аппарат предписан 7.4 п. 32"),
    Case("ответ под раскрытием", "MD033", SILENT,
         "<details>\n<summary>Ответ</summary>\n\nСервер вернёт код 200.\n\n</details>",
         why="блок 12 канона части 4 пишется через details"),

    # --- глоссарий: страничные правила ---------------------------------------
    Case("не каноническое написание", "G-CANON", CATCH,
         "Хеш argon2id считается медленно.", level="error"),
    Case("имя домена", "G-CANON", SILENT,
         "Схема описана на graphql.org в разделе про типы.",
         why="домен пишется так, как он зарегистрирован"),
    Case("цитата в «ёлочках»", "G-CANON", SILENT,
         "Раздел «Session Management Cheat Sheet» описывает срок жизни.",
         why="чужие слова: своего написания в цитате нет"),
    Case("английское имя собственное", "G-CANON", SILENT,
         "Документ OWASP Session Management Cheat Sheet описывает срок жизни.",
         why="пробег латинских слов с прописной — имя, а не термин"),
    Case("начало предложения за разметкой", "G-CANON", SILENT,
         "**Метод** GET не меняет состояние ресурса.",
         why="прописная в начале предложения законна и за `**`"),
    Case("блок источников", "G-CANON", SILENT,
         "Разбор ниже.\n\n## 14. Источники\n\n- Session — про срок жизни.",
         why="блок 14 — список чужих названий"),
    Case("аббревиатура без расшифровки", "G-FIRST", CATCH,
         "Заголовок CSP ограничивает источники скриптов.", level="warning"),
    Case("аббревиатура с расшифровкой", "G-FIRST", SILENT,
         "Политика CSP (Content Security Policy) ограничивает источники."),
    Case("русский термин с полем en", "G-FIRST", SILENT,
         "Метод GET не меняет состояние ресурса.",
         why="«метод (method)» в скобках — шум, а не раскрытие"),
    # --- заполнители шаблона: S-PLACEHOLDER -----------------------------------
    Case("заполнитель шаблона в прозе", "S-PLACEHOLDER", CATCH,
         "Ограничение снимается ⟨чем именно⟩ на границе.", level="error"),
    Case("заполнитель внутри листинга", "S-PLACEHOLDER", CATCH,
         fence(["# ⟨уязвимый фрагмент⟩"], "python"), level="error",
         why="во frontmatter и в коде заполнитель прячется лучше, чем в прозе"),
    Case("кавычки-ёлочки", "S-PLACEHOLDER", SILENT,
         "Заголовок «Set-Cookie» разбирается ниже.",
         why="⟨…⟩ — не «…»: правило смотрит на угловые скобки, а не на кавычки"),
    Case("автоссылка и тег details", "S-PLACEHOLDER", SILENT,
         "Адрес <https://example.com/a> и <details> на месте.",
         why="ASCII-угол `<` законен: это автоссылка и разрешённый HTML"),
    Case("термин вводит сама тема", "G-FIRST", SILENT,
         "Заголовок CSP ограничивает источники скриптов.", page_id="csp",
         why="условие 3: страница названа в defines термина"),
    Case("раскрыто в предпосылке", "G-FIRST", SILENT,
         "Заголовок CSP ограничивает источники скриптов.", prereq=("csp",),
         why="условие 4: тема-предпосылка уже ввела термин"),
    Case("ссылка вперёд в блоке 13", "G-FIRST", SILENT,
         "Разбор ниже.\n\n## 13. Дальше\n\n- `security-headers` — HSTS и соседи.",
         why="блок 13 говорит о других страницах, а не о материале этой"),
]


# ── прогон инструментов ──────────────────────────────────────────────────────

PAGE = """---
id: {page_id}
title: 'Фикстура {n}'
stage: fixtures
order: {order}
depth: L2
prerequisites: [{prereq}]
---

# Фикстура {n}

## 2. Разбор

{body}
"""


def write_fixtures(tmp: Path) -> list[tuple[Case, Path]]:
    out = []
    for i, case in enumerate(CASES):
        path = tmp / f"{i:02d}.md"
        path.write_text(
            PAGE.format(n=i, order=900 + i, body=case.body,
                        page_id=case.page_id or f"fx-{i:02d}",
                        prereq=", ".join(case.prereq)),
            encoding="utf-8")
        out.append((case, path))
    return out


def collect(fixtures) -> dict[str, list]:
    """Все замечания по фикстурам: инструменты — теми же вызовами, что в check.py."""
    paths = [check.rel(str(p)) for _c, p in fixtures]
    results = [check.vale(paths),
               check.markdownlint(paths),
               check.own("style", "lint_style.py", paths)]
    broken = [r for r in results if not r.ok]
    if broken:
        for r in broken:
            sys.stderr.write(f"инструмент {r.name} не отработал: {r.note}\n")
        sys.exit(2)

    findings = [f for r in results for f in r.findings]

    # Глоссарий смотрит на набор страниц целиком, поэтому вызывается напрямую:
    # фикстуры образуют свой маленький «сайт» со своим порядком и предпосылками.
    _data, terms, _groups, _lines = gl.load_glossary()
    pages = []
    for _case, path in fixtures:
        doc = mdtext.load(path)
        import yaml
        front = yaml.safe_load(doc.front_text) if doc.front_text else {}
        pages.append((path, doc, front))
    pages.sort(key=lambda p: (p[2].get("order", 10 ** 9), p[2].get("id", "")))
    regexes = gl.term_regexes(terms)
    hits = gl.first_hits(pages, regexes, material_only=True)
    findings += gl.check_canon(pages, gl.build_canon(terms))
    findings += gl.check_first(pages, terms, regexes, hits)

    by_path: dict[str, list] = {}
    for f in findings:
        by_path.setdefault(check.rel(str(f.path)), []).append(f)
    return by_path


def verdict(case: Case, found: list) -> str:
    """Пустая строка — утверждение сошлось, иначе причина расхождения."""
    if case.rule == ANY:
        if found:
            names = ", ".join(sorted({f.rule for f in found}))
            return f"сработало: {names}"
        return ""
    mine = [f for f in found if f.rule == case.rule]
    if case.mode == SILENT:
        return f"сработало {len(mine)} раз" if mine else ""
    if not mine:
        others = ", ".join(sorted({f.rule for f in found})) or "тишина"
        return f"не сработало ({others})"
    if case.count and len(mine) != case.count:
        return f"сработало {len(mine)} раз вместо {case.count}"
    if case.level and not any(f.level == case.level for f in mine):
        got = ", ".join(sorted({f.level for f in mine}))
        return f"уровень {got} вместо {case.level}"
    return ""


# ── проверки уровня данных ───────────────────────────────────────────────────

def term(tid, term_name, group="protocol", **kw):
    t = {"id": tid, "term": term_name, "group": group,
         "definition": "Определение для фикстуры."}
    t.update(kw)
    return t


def data_cases() -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — глоссарий как данные, без файлов."""
    groups = {"protocol": "Протокол"}
    pages = {"http-basics"}

    def gloss(terms):
        return gl.check_glossary(terms, groups, {}, pages)

    out = [
        ("повтор идентификатора", "G-GLOSS", CATCH,
         gloss([term("a", "первый"), term("a", "второй")])),
        ("группа не объявлена", "G-GLOSS", CATCH,
         gloss([term("a", "первый", group="нет-такой")])),
        ("пустое определение", "G-GLOSS", CATCH,
         gloss([{"id": "a", "term": "первый", "group": "protocol",
                 "definition": "  "}])),
        ("see_also в никуда", "G-GLOSS", CATCH,
         gloss([term("a", "первый", see_also=["нет-такого"])])),
        ("defines в никуда", "G-GLOSS", CATCH,
         gloss([term("a", "первый", defines=["нет-такой-темы"])])),
        ("одно написание на два термина", "G-SYNSET", CATCH,
         gloss([term("a", "маркер"), term("b", "Маркер")])),
        ("дефис значим", "G-SYNSET", SILENT,
         gloss([term("a", "SameSite"), term("b", "same-site")])),
        ("термин не употреблён", "G-UNUSED", CATCH,
         gl.check_unused([term("a", "первый")], {"p": {}}, {})),
        ("термин употреблён", "G-UNUSED", SILENT,
         gl.check_unused([term("a", "первый")], {"p": {"a": 0}}, {})),
    ]

    # Настоящий глоссарий: целостность — блокирующая проверка 9.4.
    data, terms, groups_real, lines = gl.load_glossary()
    page_ids = {f.get("id", p.stem) for p, _d, f in gl.load_pages()}
    real = gl.check_glossary(terms, groups_real, lines, page_ids)
    out.append(("настоящий glossary.yaml", "G-GLOSS", SILENT, real))
    out.append(("настоящий glossary.yaml", "G-SYNSET", SILENT, real))
    return out


# ── контентная модель: правила C-* ───────────────────────────────────────────
#
# `validate_content.py` всегда читает `content/**` целиком — цикл в графе и
# занятый `order` иначе не увидеть. Подкладывать в корпус испорченные темы
# нельзя, поэтому фикстуры зовут проверки напрямую: правила уровня страницы —
# функции от `(Page, Ctx)`, правила уровня корпуса — от списка страниц. Базой
# берётся живая тема L1 со полным скелетом: мутация одного места на настоящем
# тексте проверяет и правило, и то, что оно молчит на всём остальном.

BASE_PAGE = Path("content/stage-1/password-storage.md")


class Nothing:
    """Заглушка для фикстуры, чья мутация не применилась."""

    rule = "МУТАЦИЯ-НЕ-ПРИМЕНИЛАСЬ"
    level = "error"


def model_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — контентная модель на мутациях темы."""
    ctx = vc.Ctx()
    base = BASE_PAGE.read_text(encoding="utf-8")
    # Дата ревизии берётся из самой темы, а не пишется здесь числом: тему
    # перечитывают, дата съезжает, и пять мутаций про `reviewed` перестают
    # применяться молча — самопроверка при этом печатает не «правило сломано», а
    # «МУТАЦИЯ-НЕ-ПРИМЕНИЛАСЬ» (замер 2026-08-23: ровно так и вышло после
    # правки шапки темы).
    seen = re.search(r"(?m)^reviewed: (\d{4}-\d\d-\d\d)$", base)
    assert seen, f"{BASE_PAGE}: нет поля reviewed — мутации не построить"
    REV = seen.group(1)
    # Каталог этапа сохраняется: иначе C-FM-STAGE-DIR сработает на каждой
    # фикстуре и утонет в выводе всё остальное.
    home = tmp / "model" / ctx.stages["web-vulns"]["dir"]
    home.mkdir(parents=True, exist_ok=True)
    target = home / BASE_PAGE.name

    def page_of(text: str):
        target.write_text(text, encoding="utf-8")
        return vc.read_page(target)

    def one(text: str) -> list:
        """Все замечания уровня страницы по мутированному тексту."""
        if text == base:
            return [Nothing()]
        page = page_of(text)
        return (vc.check_front(page, ctx) + vc.check_head(page, ctx)
                + vc.check_blocks(page, ctx) + vc.check_body(page, ctx))

    def sub(old_text: str, new_text: str, count: int = -1) -> list:
        return one(base.replace(old_text, new_text)
                   if count < 0 else base.replace(old_text, new_text, count))

    def sub_re(pattern: str, repl: str) -> list:
        """Мутация по выражению — там, где в тексте темы стоит невидимый знак.

        Между числом и единицей в шапке живёт неразрывный пробел (6.4, правило
        `L-NBSP`), и написанный здесь литерал «время 90 мин» с обычным пробелом
        перестаёт применяться молча: самопроверка печатает не «правило
        сломано», а «МУТАЦИЯ-НЕ-ПРИМЕНИЛАСЬ» (замер 2026-08-23: ровно так и
        вышло после механического прохода по неразрывным пробелам). Тот же
        приём, что с датой ревизии в `REV`: признак берётся из темы, а не
        переписывается здесь руками.
        """
        return one(re.sub(pattern, repl, base))

    def cut(start: str, stop: str) -> list:
        """Убрать кусок текста от одного маркера до другого."""
        i, j = base.find(start), base.find(stop)
        return one(base if i < 0 or j < i else base[:i] + base[j:])

    def corpus(mutate) -> list:
        """Замечания уровня корпуса: страницы живые, frontmatter подменён."""
        pages = [copy.copy(p) for p in vc.load_pages()]
        for p in pages:
            p.front = dict(p.front)
        mutate({p.id: p for p in pages})
        return vc.check_refs(pages, ctx)

    def elsewhere() -> list:
        """Та же тема, но в каталоге другого этапа."""
        alien = tmp / "model" / ctx.stages["appsec-tooling"]["dir"]
        alien.mkdir(parents=True, exist_ok=True)
        dest = alien / BASE_PAGE.name
        dest.write_text(base, encoding="utf-8")
        return vc.check_front(vc.read_page(dest), ctx)

    def downgraded() -> list:
        """L1-тема, объявленная L2: блоки 2, 7 и 8 на L2 не предусмотрены."""
        return one(base.replace("depth: L1", "depth: L2")
                       .replace("уровень **L1**", "уровень **L2**")
                       .replace("полный по уровню L1", "полный по уровню L2"))

    def corpus_text(page_id: str, old_text: str, new_text: str) -> list:
        """Мутация прозы одной темы: ссылки на план живут в тексте, не в полях."""
        pages = vc.load_pages()
        for i, page in enumerate(pages):
            if page.id != page_id:
                continue
            target_page = home / f"{page_id}.md"
            text = Path(page.path).read_text(encoding="utf-8")
            if old_text not in text:
                return [Nothing()]
            target_page.write_text(text.replace(old_text, new_text),
                                   encoding="utf-8")
            pages[i] = vc.read_page(target_page)
            break
        return vc.check_refs(pages, ctx)

    def swap_blocks(first: str, second: str) -> list:
        """Поменять два блока местами, сохранив их содержимое."""
        ia, ib = base.find(first), base.find(second)
        end = base.find("\n## ", ib + 1)
        return one(base[:ia] + base[ib:end] + base[ia:ib] + base[end:])

    clean = one(base + "\n")
    out = [
        # живая тема проверки проходит: без этого все «ловит» ниже ничего не
        # доказывают — они могли бы срабатывать на самом тексте
        ("настоящая тема L1", ANY, SILENT, clean),

        # --- frontmatter -----------------------------------------------------
        ("нет обязательного поля", "C-FM-REQUIRED", CATCH,
         sub("mode: концепт\n", "")),
        ("поле вне схемы", "C-FM-UNKNOWN", CATCH,
         sub("order: 480\n", "order: 480\nnext: [x]\n")),
        ("поля не в порядке схемы", "C-FM-SEQ", CATCH,
         sub("status: draft\ndepth: L1", "depth: L1\nstatus: draft")),
        ("условные поля на своём месте", "C-FM-SEQ", SILENT,
         sub(f"reviewed: {REV}\nreview_interval",
             f"derived_from: [python-hashlib]\nupdated: {REV}\n"
             f"reviewed: {REV}\nreview_interval", 1),
         "`derived_from` и `updated` — условные поля 9.3 и 9.6 п. 19"),
        ("не тот тип значения", "C-FM-TYPE", CATCH,
         sub("time_min: 90", "time_min: девяносто")),
        ("id не kebab-case", "C-FM-ID", CATCH,
         sub("id: password-storage", "id: Password_Storage")),
        ("plan_id не в плане", "C-FM-PLAN", CATCH,
         sub("plan_id: t-1-6-07", "plan_id: t-9-9-99")),
        ("title не совпадает с h1", "C-FM-TITLE", CATCH,
         sub("# Хранение паролей: bcrypt, argon2, почему не SHA",
             "# Пароли", 1)),
        ("тег вне словаря", "C-FM-VOCAB", CATCH,
         sub("tags: [auth,", "tags: [нетакого,")),
        ("order не кратен 10", "C-FM-ORDER", CATCH, sub("order: 480", "order: 485")),
        ("цель со строчной буквы", "C-FM-TEACHES", CATCH,
         sub("  - Назвать, что даёт соль", "  - назвать, что даёт соль")),
        ("тема в своих предпосылках", "C-FM-PREREQ", CATCH,
         sub("prerequisites: [", "prerequisites: [password-storage, ")),
        ("идентификатор не той формы", "C-FM-IDENT", CATCH,
         sub("cwe: [CWE-916", "cwe: [CWE916")),
        ("источник не в реестре", "C-REF-SOURCE", CATCH,
         sub("sources: [owasp-cs-password-storage", "sources: [нет-такого")),
        ("derived_from вне реестра", "C-REF-SOURCE", CATCH,
         sub(f"reviewed: {REV}\nreview_interval",
             f"derived_from: [нет-такого]\nreviewed: {REV}\nreview_interval", 1)),
        ("лаба не в реестре", "C-REF-LAB", CATCH,
         sub("labs: [lab-password-storage]", "labs: [lab-нет-такой]")),
        ("reviewed в будущем", "C-FM-DATE", CATCH,
         sub(f"reviewed: {REV}\nreview_interval",
             "reviewed: 2027-01-01\nreview_interval", 1)),
        ("reviewed в будущем", "C-FM-DATE", CATCH,
         sub(f"reviewed: {REV}\nreview_interval",
             "reviewed: 2027-01-01\nreview_interval", 1)),
        ("title длиннее 60 символов", "C-FM-TITLE-LEN", CATCH,
         sub("title: 'Хранение паролей: bcrypt, argon2, почему не SHA'\n"
             "summary:",
             "title: 'Хранение паролей: bcrypt, argon2, scrypt, PBKDF2 и почему "
             "не SHA, если коротко'\nsummary:")),
        ("summary не 1–2 предложения", "C-FM-SUMMARY", CATCH,
         sub("  после утечки дампа и чем цена догадки задаётся в коде.\n",
             "  после утечки дампа. Чем цена задаётся в коде. Что делать. "
             "Куда смотреть.\n")),
        ("смежных больше пяти", "C-FM-RELATED", CATCH,
         sub("related: [sessions-vs-tokens, tls-and-proxy]",
             "related: [sessions-vs-tokens, tls-and-proxy, cookies, csp, cors, "
             "http-basics]")),
        ("источников меньше двух", "C-FM-SOURCES", CATCH,
         sub("sources: [owasp-cs-password-storage, nist-sp-800-63b, "
             "wstg-v42-cryp-04-weak-encryption, rfc9106-argon2, python-hashlib, "
             "node-crypto]", "sources: [python-hashlib]")),
        ("ревизия просрочена", "C-FM-REVIEW", CATCH,
         sub(f"reviewed: {REV}\nreview_interval: 24",
             "reviewed: 2020-01-01\nreview_interval: 24", 1)),

        # --- шапка -----------------------------------------------------------
        ("категория кода вне словаря", "C-HEAD-CODE", CATCH,
         sub("**AG-AUTH-07**", "**AG-XXX-07**")),
        ("номер кода не из plan_id", "C-HEAD-CODE", CATCH,
         sub("**AG-AUTH-07**", "**AG-AUTH-09**")),
        ("уровень в шапке другой", "C-HEAD-DEPTH", CATCH,
         sub("уровень **L1**", "уровень **L2**")),
        ("время в шапке другое", "C-HEAD-TIME", CATCH,
         sub_re(r"время 90(\s)мин", r"время 95\1мин")),
        ("слагаемые времени не дают суммы", "C-HEAD-TIME", CATCH,
         sub("(теория 40 / лаба 35", "(теория 40 / лаба 30")),
        ("reviewed в шапке другой", "C-HEAD-REVIEWED", CATCH,
         sub(f"· reviewed: {REV} ·", "· reviewed: 2026-01-01 ·")),
        ("нет «проверено на:»", "C-HEAD-VERSIONS", CATCH,
         sub("· проверено на:", "· стек:")),
        ("нет версии каталога CWE", "C-HEAD-VERSIONS", CATCH,
         sub(", CWE 4.20\n", "\n", 1)),
        ("пререквизиты в шапке другие", "C-HEAD-PREREQ", CATCH,
         sub("пререквизиты: `app-architecture`, `sessions-vs-tokens`",
             "пререквизиты: `app-architecture`")),
        ("CWE потерян в маппинге", "C-HEAD-MAP", CATCH,
         sub("маппинг: CWE-916 ·\nCWE-759 ·", "маппинг: CWE-916 ·")),

        # --- скелет ----------------------------------------------------------
        ("блок назван не по канону", "C-BLOCK-TITLE", CATCH,
         sub("## 9. Ловушка", "## 9. Западня")),
        ("блоки переставлены", "C-BLOCK-ORDER", CATCH,
         swap_blocks("## 9. Ловушка", "## 10. Чеклист ревью")),
        ("нет обязательного блока", "C-BLOCK-REQ", CATCH,
         cut("## 7. Как проверить фикс", "## 8. Как ловится")),
        ("декларация не про этот уровень", "C-DECL", CATCH,
         sub("полный по уровню L1", "полный по уровню L2")),
        ("заголовок блока не нумерован", "C-BLOCK-SHAPE", CATCH,
         sub("## 9. Ловушка", "## Ловушка")),
        ("номер блока вне скелета", "C-BLOCK-NUM", CATCH,
         sub("## 9. Ловушка", "## 19. Ловушка")),
        ("декларация врёт про удаления", "C-DECL-SET", CATCH,
         sub("удалений нет", "блок 3 удалён")),

        # --- наполнение ------------------------------------------------------
        ("нет абзаца «зачем»", "C-BODY-WHY", CATCH,
         sub("**Зачем это в работе AppSec-инженера.**", "**Зачем.**", 1)),
        ("нет маркеров уверенности", "C-BODY-TRUST", CATCH,
         sub("**Маркеры уверенности.**", "**Маркеры.**", 1)),
        ("нет «откуда это взялось»", "C-BODY-ORIGIN", CATCH,
         sub("**Откуда это взялось.**", "**Как до этого дошли.**", 1)),
        ("цель не про то же", "C-BODY-GOALS", CATCH,
         sub("  - Назвать, что даёт соль и чего она не даёт\n",
             "  - Совершенно посторонняя формулировка ни о чём\n")),
        ("цель пересказана", "C-BODY-GOALS", SILENT,
         sub("  - Назвать, что даёт соль и чего она не даёт\n",
             "  - Назвать, что соль даёт и чего не даёт\n"),
         "`teaches` — короткая форма, блок 1 — фраза для читателя (`SCHEMA.md` § 6)"),
        ("пункт чеклиста не в залоге", "C-BODY-CHECKLIST", CATCH,
         sub("1. Verify that", "1. Убедитесь, что", 1)),
        ("нет ответов под раскрытием", "C-BODY-SELFCHECK", CATCH,
         sub("<details>", "<detailz>")),
        ("пункт «дальше» без ссылки", "C-BODY-NEXT", CATCH,
         sub("## 13. Дальше\n\n-", "## 13. Дальше\n\n- просто текст\n-", 1)),
        ("сноска и sources расходятся", "C-BODY-SOURCES", CATCH,
         sub("`python-hashlib`", "`mdn-csp`")),
        ("каркас этапа не в sources", "C-BODY-SOURCES", SILENT, clean,
         "источники этапа названы прозой после сносок и в `sources` не дублируются"),
        ("идентификатор в тексте не объявлен", "C-BODY-IDENT", CATCH,
         sub("cwe: [CWE-916", "cwe: [CWE-917", 1)),
        ("идентификатор объявлен и не напечатан", "C-BODY-IDENT", CATCH,
         sub("wstg: ['WSTG-v42-CRYP-04']", "wstg: ['WSTG-v42-CRYP-04', "
             "'WSTG-v42-CRYP-01']", 1)),

        # --- фикстуры особой формы -------------------------------------------
        # Каталог этапа проверяется положением файла, а не текстом: тема
        # переезжает в чужой каталог без правки самой темы.
        ("тема в чужом каталоге", "C-FM-STAGE-DIR", CATCH, elsewhere()),
        # Блок 4 на L2 разрешён, а блоки 2, 7 и 8 — нет (`SCHEMA.md` § 4).
        # Проверяется на L2-теме: спуск L1 до L2 сразу даёт четыре лишних блока.
        ("блок не по уровню", "C-BLOCK-EXTRA", CATCH, downgraded()),

        # --- корпус ----------------------------------------------------------
        ("id занят другой темой", "C-FM-ID", CATCH,
         corpus(lambda d: d["cookies"].front.__setitem__("id", "csp"))),
        ("order занят внутри этапа", "C-FM-ORDER", CATCH,
         corpus(lambda d: d["cookies"].front.__setitem__(
             "order", d["csp"].front["order"]))),
        ("этап не совпадает с plan_id", "C-FM-PLAN", CATCH,
         corpus(lambda d: d["cookies"].front.__setitem__("stage", "appsec-tooling"))),
        ("ссылка на несуществующую тему", "C-REF-TOPIC", CATCH,
         corpus(lambda d: d["cookies"].front.__setitem__(
             "prerequisites", ["нет-такой-темы"]))),
        ("цикл в графе предпосылок", "C-REF-CYCLE", CATCH,
         corpus(lambda d: (d["cookies"].front.__setitem__("prerequisites", ["csp"]),
                           d["csp"].front.__setitem__("prerequisites", ["cookies"])))),
        ("настоящий корпус: циклов нет", "C-REF-CYCLE", SILENT, corpus(lambda d: None)),
        ("настоящий корпус: ссылки целы", "C-REF-TOPIC", SILENT, corpus(lambda d: None)),
        ("настоящий корпус: план сходится", "C-REF-PLAN", SILENT, corpus(lambda d: None)),
        ("ссылка на номер вне плана", "C-REF-PLAN", CATCH,
         corpus_text("cookies", "в подразделе 1.5", "в подразделе 1.99")),
        ("тема без входящих ссылок", "C-REF-ORPHAN", CATCH,
         corpus(lambda d: [p.front.__setitem__(
             "prerequisites", [x for x in p.front.get("prerequisites") or []
                               if x != "cookies"])
             or p.front.__setitem__(
                 "related", [x for x in p.front.get("related") or []
                             if x != "cookies"])
             for p in d.values()])),
    ]
    return out


# ── объём: правила C-VOL-* ───────────────────────────────────────────────────
#
# Правило объёма проверяется не выдуманной темой, а живой: норма считается по
# методу свода 3.1, и весь смысл фикстуры — в том, что метод отбрасывает именно
# служебный аппарат и ничего кроме. Базой берётся L1-тема (2657 слов текста при
# норме 2500–3500): её объём внутри нормы, поэтому и «молчит», и «ловит»
# проверяются мутацией одного места.


class Rec:
    """Замечание `wordcount.py` в виде объекта: селф-тест читает `.rule`."""

    def __init__(self, d: dict):
        self.rule, self.level = d["rule"], d["level"]


def volume_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — объём на мутациях живой темы."""
    base = BASE_PAGE.read_text(encoding="utf-8")
    home = tmp / "volume"
    home.mkdir(parents=True, exist_ok=True)
    target = home / BASE_PAGE.name

    def one(text: str) -> list:
        target.write_text(text, encoding="utf-8")
        return [Rec(d) for d in wcnt.check(target)[2]]

    def sub(old_text: str, new_text: str, count: int = -1) -> list:
        return one(base.replace(old_text, new_text)
                   if count < 0 else base.replace(old_text, new_text, count))

    # Абзац настоящими словами, повторённый столько раз, чтобы гарантированно
    # перешагнуть верх нормы L1 от текущего объёма темы: фикстура не должна
    # ломаться от того, что тема подросла на сотню слов.
    para = ("Пароль проверяется на сервере, и проверка стоит времени. " * 4).strip()
    here = wcnt.counts(base)[2]
    times = 2 + max(0, wcnt.NORM["L1"][1] - here) // len(wcnt.WORD.findall(para))
    grow = "\n\n".join([para] * times)
    short = base[: base.find("## 3.")] + "## 14. Источники\n"
    return [
        ("живая тема L1 внутри нормы", "C-VOL-OVER", SILENT, one(base),
         f"{here} слов текста при норме 2500–3500"),
        ("живая тема L1 внутри нормы", "C-VOL-UNDER", SILENT, one(base)),
        ("уровень темы распознан", "C-VOL-DEPTH", SILENT, one(base)),
        ("тема выше нормы уровня", "C-VOL-OVER", CATCH,
         sub("## 14.", grow + "\n\n## 14.", 1)),
        ("тема ниже нормы уровня", "C-VOL-UNDER", CATCH, one(short)),
        ("уровень не из словаря", "C-VOL-DEPTH", CATCH, sub("depth: L1", "depth: L9")),
        # Служебный аппарат: каждая его часть обязана выпасть из подсчёта.
        # Признак один и тот же — кусок дописан, а вердикт не сдвинулся.
        ("блок 14 и всё за ним не считаются", "C-VOL-OVER", SILENT,
         sub("## 14.", "## 14. Источники\n\n" + grow + "\n\n## 14.", 1),
         f"приписка на {times * 36} слов за блоком 14 не сдвигает вердикт"),
        ("листинг не считается", "C-VOL-OVER", SILENT,
         sub("## 13. Дальше", "```text\n" + grow + "\n```\n\n## 13. Дальше", 1),
         "листинг того же объёма не сдвигает вердикт"),
        # Блок идентификации кончается первой пустой строкой, поэтому дописка в
        # него идёт одним абзацем: с пустой строкой внутри это была бы уже проза.
        ("блок идентификации не считается", "C-VOL-OVER", SILENT,
         sub("**AG-AUTH-07**", "**AG-AUTH-07** " + " ".join([para] * times), 1),
         "дописанное в шапку под заголовком выпадает вместе с ней"),
        # Свод 3.1 п. 8 (решение оператора от 2026-08-23): два обязательных
        # абзаца в норму не входят. Проверяется тем же приёмом — абзац растёт,
        # вердикт стоит на месте.
        ("абзац «Зачем это в работе» не считается", "C-VOL-OVER", SILENT,
         sub("**Зачем это в работе AppSec-инженера.**",
             "**Зачем это в работе AppSec-инженера.** " + " ".join([para] * times), 1),
         "дописанное во врезку «Зачем это в работе» выпадает вместе с ней"),
        ("абзац «Откуда это взялось» не считается", "C-VOL-OVER", SILENT,
         sub("**Откуда это взялось.**",
             "**Откуда это взялось.** " + " ".join([para] * times), 1),
         "дописанное во врезку «Откуда это взялось» выпадает вместе с ней")]


# ── ссылки: правила S-LINK-* и S-EXT-IN-BODY ─────────────────────────────────
#
# Тот же приём, что у контентной модели: базой берётся живая тема, мутируется
# одно место. База здесь другая — `cookies`: у неё в блоке 13 есть и ссылка
# идентификатором, и ссылка номером плана, а в блоке 14 — две сноски с
# автоссылками, то есть все проверяемые формы сразу.

BASE_LINK_PAGE = Path("content/stage-0/cookies.md")


def link_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — ссылки на мутациях живой темы."""
    base = BASE_LINK_PAGE.read_text(encoding="utf-8")
    ids = lc.load_ids([])
    source_urls = lc.load_source_urls()
    home = tmp / "links"
    home.mkdir(parents=True, exist_ok=True)
    target = home / BASE_LINK_PAGE.name

    def one(text: str) -> list:
        if text == base:
            return [Nothing()]
        target.write_text(text, encoding="utf-8")
        doc = mdtext.load(target)
        marks = lc.blocks_of(doc)
        return (lc.check_external_placement(target, doc, marks)
                + lc.check_source_urls(target, doc, marks, source_urls)
                + lc.check_topic_refs(target, doc, marks, ids)
                + lc.check_md_links(target, doc, ids))

    def sub(old_text: str, new_text: str, count: int = -1) -> list:
        return one(base.replace(old_text, new_text)
                   if count < 0 else base.replace(old_text, new_text, count))

    def after_head(added: str) -> list:
        """Вставить текст в блок 3 «Механика» — середина материала темы."""
        return sub("## 3. Механика", "## 3. Механика\n\n" + added + "\n", 1)

    mdn = "<https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies>"
    out = [
        ("адрес в блоке 3", "S-EXT-IN-BODY", CATCH,
         after_head("Подробности — <https://example.org/spec>.")),
        ("адрес в шапке", "S-EXT-IN-BODY", CATCH,
         sub("**AG-PROTO-03**", "<https://example.org/x> **AG-PROTO-03**", 1)),
        ("адрес в блоке 14", "S-EXT-IN-BODY", SILENT, one(base + "\n"),
         "автоссылки настоящей темы стоят там, где им можно"),
        ("адрес примером в коде", "S-EXT-IN-BODY", SILENT,
         after_head("Например, `https://evil.com/a` в поле."),
         "инлайновый код — не ссылка"),

        ("сноска без угловых скобок", "S-LINK-BARE", CATCH,
         sub(mdn, mdn[1:-1], 1)),
        ("адрес в обратных кавычках", "S-LINK-BARE", SILENT,
         after_head("Пример: `https://evil.com/a`."),
         "в коде адрес ссылкой и не должен становиться"),

        ("пункт блока 13 в никуда", "S-LINK-TOPIC", CATCH,
         sub("- `sessions-vs-tokens` —", "- `net-takoy-temy` —", 1)),
        ("возврат к теме в никуда", "S-LINK-TOPIC", CATCH,
         sub("Возврат к теме `http-basics`", "Возврат к теме `net-takoy-temy`", 1)),
        ("«в этой теме `Set-Cookie`»", "S-LINK-TOPIC", SILENT,
         after_head("В этой теме `Set-Cookie` разбирается ниже."),
         "«эта тема» — сама страница, код после неё называет поле"),
        ("«в теме `SameSite`»", "S-LINK-TOPIC", SILENT,
         after_head("В теме `SameSite` описан ниже."),
         "форме идентификатора не отвечает: прописные буквы"),

        ("ссылка на пропавший файл", "S-LINK-MD", CATCH,
         after_head("Разбор — [здесь](missing.md).")),
        ("ссылка на чужой анкорь", "S-LINK-MD", CATCH,
         after_head("Разбор — [здесь](#net-takogo-ankorya).")),
        ("ссылка с пустой целью", "S-LINK-MD", CATCH,
         after_head("Разбор — [здесь]().")),
        ("ссылка на живой анкорь", "S-LINK-MD", SILENT,
         after_head("Разбор — [здесь](#3-механика)."),
         "анкорь совпадает с заголовком блока 3"),
        ("внешний адрес markdown-ссылкой", "S-LINK-MD", SILENT,
         after_head("Разбор — [здесь](https://example.org/x)."),
         "внешним занимается S-EXT-IN-BODY, а не это правило"),

        ("сноска ведёт мимо реестра", "S-LINK-SOURCE-URL", CATCH,
         sub(mdn, "<https://developer.mozilla.org/en-US/docs/Web/HTTP>", 1)),
        ("сноска совпала с реестром", "S-LINK-SOURCE-URL", SILENT,
         one(base + "\n"), "настоящая тема: адрес сноски и `url` записи совпадают"),

        ("настоящая тема целиком", ANY, SILENT, one(base + "\n")),
    ]

    # Внешние адреса. Хост в зоне `.invalid` не разрешается никогда (RFC 2606),
    # поэтому «ловит» проверяется без сети. «Молчит» проверяется на подменённой
    # `probe`: утверждение здесь про обвязку — что пустой ответ проверки не
    # превращается в замечание, — а не про доступность чужого сайта.
    dead = [(str(target), 1, 1, "http://ne-razreshaetsya-nikogda.invalid/x")]
    out.append(("адрес не открылся", "S-LINK-EXT", CATCH,
                lc.check_external(dead, timeout=5.0, workers=1)))
    saved = lc.probe
    try:
        lc.probe = lambda url, timeout, tries=2: ""
        out.append(("адрес открылся", "S-LINK-EXT", SILENT,
                    lc.check_external(dead, timeout=5.0, workers=1)))
    finally:
        lc.probe = saved
    return out


# ── печать ───────────────────────────────────────────────────────────────────

# ── шаблоны уровней ──────────────────────────────────────────────────────────
# Шаблон — не украшение: тема, начатая с него, обязана быть зелёной до первой
# авторской правки. Иначе автор с первого же прогона учится не читать вывод.
# Проверяется тем же кодом, что и корпус: шаблон кладётся в дерево под своим
# `id` и в каталог своего этапа, и по нему прогоняются все правила уровня
# страницы. Правила уровня корпуса (`C-REF-*`, уникальность `order`) — свойства
# набора страниц, а не шаблона, и здесь не зовутся.


class NoTemplate:
    """Заглушка: у уровня из словаря нет файла шаблона."""

    rule = "ШАБЛОНА-НЕТ"
    level = "error"


def template_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — шаблоны уровней L1, L2, L3."""
    ctx = vc.Ctx()
    staging = tmp / "tpl-raw"
    staging.mkdir(parents=True, exist_ok=True)
    out: list[tuple[str, str, str, list]] = []
    for depth in sorted(ctx.depths):
        src = Path("templates") / f"{depth}.md"
        name = f"шаблон {depth}"
        if not src.exists():
            out.append((f"{name} существует", ANY, SILENT, [NoTemplate()]))
            continue
        text = src.read_text(encoding="utf-8")
        probe = staging / src.name
        probe.write_text(text, encoding="utf-8")
        front = vc.read_page(probe).front
        home = tmp / "tpl" / ctx.stages[front.get("stage", "")]["dir"]
        home.mkdir(parents=True, exist_ok=True)
        dest = home / f"{front.get('id', 'no-id')}.md"
        dest.write_text(text, encoding="utf-8")
        page = vc.read_page(dest)
        found = (vc.check_front(page, ctx) + vc.check_head(page, ctx)
                 + vc.check_blocks(page, ctx) + vc.check_body(page, ctx))
        # `C-FM-REVIEW` снято: дата ревизии в шаблоне зафиксирована в файле и
        # неизбежно устареет, а предупреждение о просрочке — про живую тему.
        # Всё остальное, включая ошибки формы даты, проверяется как есть.
        found = [f for f in found if f.rule != "C-FM-REVIEW"]
        out.append((f"{name} как тема", ANY, SILENT, found,
                    "все правила модели молчат: тема начинается зелёной"))
        out.append((f"{name} размечен ⟨…⟩", "S-PLACEHOLDER", CATCH,
                    ls.check_placeholder(dest, mdtext.load(dest)),
                    "заполнители шаблона — та же разметка, которую ловит правило"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quiet", action="store_true", help="только провалы и итог")
    ap.add_argument("--keep", action="store_true", help="оставить фикстуры на диске")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="lint-selftest-"))
    failures = []
    try:
        fixtures = write_fixtures(tmp)
        by_path = collect(fixtures)
        rows = []
        for case, path in fixtures:
            found = by_path.get(check.rel(str(path)), [])
            rows.append((case.rule, case.mode, case.name, case.why,
                         verdict(case, found), path))
        for name, rule, mode, found in data_cases():
            case = Case(name, rule, mode, "")
            rows.append((rule, mode, name, "", verdict(case, found), None))
        for row in (list(model_cases(tmp)) + list(volume_cases(tmp))
                    + list(link_cases(tmp)) + list(template_cases(tmp))):
            name, rule, mode, found = row[:4]
            why = row[4] if len(row) > 4 else ""
            case = Case(name, rule, mode, "")
            rows.append((rule, mode, name, why, verdict(case, found), None))

        for rule, mode, name, why, bad, path in rows:
            if bad:
                failures.append((rule, name, bad, path))
                print(f"  ПРОВАЛ  {rule:<14} {mode}  {name}: {bad}")
            elif not args.quiet:
                tail = f"  — {why}" if why else ""
                print(f"  ок      {rule:<14} {mode}  {name}{tail}")

        total = len(rows)
        print(f"\nИТОГ: {total - len(failures)} из {total} утверждений сошлись"
              + (" — не пройдено" if failures else " — пройдено"))
        if failures and not args.keep:
            print(f"фикстуры: {tmp} (оставлены для разбора)")
        return 1 if failures else 0
    finally:
        if not failures and not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)
        elif args.keep:
            print(f"фикстуры: {tmp}")


if __name__ == "__main__":
    sys.exit(main())
