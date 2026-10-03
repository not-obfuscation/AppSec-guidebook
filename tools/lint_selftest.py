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
import datetime as dt
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check
import glossary_lint as gl
import lint_code as lcd
import lint_style as ls  # noqa: F401  — импорт держит зависимость явной
import mdtext
import linkcheck as lc
import validate_content as vc
import wordcount as wcnt
from paths import CONTENT_DIR, TEMPLATES_DIR

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
    Case("местоимение «данные» во множественном", "L-CLERICAL2", CATCH,
         "В данных условиях запрос уходит без проверки, и данные меры не помогают.",
         level="warning", count=2),
    Case("существительное «данные»", "L-CLERICAL2", SILENT,
         "Разделение кода и данных: данные едут отдельным параметром, "
         "отчёт фильтрует данные методами ORM, а работа с данными структуру "
         "запроса не меняет.",
         why="«данные» — существительное на каждой странице гайда; правило "
             "ловит оборот канцелярита, а не словоформу"),
    Case("обесценивающее слово", "L-BANNED", CATCH,
         "Такой запрос просто уходит на сервер."),
    Case("форма слова «проставить»", "L-BANNED", SILENT,
         "Оценку проставить должен ревьюер, а поля проставлены заранее.",
         why="«проставить» — не форма «просто»: после «проста» стоит «в» "
             "(заявка З-3)"),
    Case("оценка без факта", "L-EVAL", CATCH,
         "Схема удобная для разбора."),
    Case("вводный штамп", "L-FILLER", CATCH,
         "Стоит отметить, что заголовок обязателен."),
    Case("навигация словом", "L-NAV", CATCH,
         "Разбор лежит [здесь](#razbor)."),
    Case("время без даты", "L-TIMELESS", CATCH,
         "Сейчас браузер отклоняет такой ответ.", level="warning"),
    Case("якорь «на сегодня» без «шний день»", "L-TIMELESS", CATCH,
         "Полного решения задачи на сегодня нет.", level="warning"),
    Case("привязка к изданию вместо якоря", "L-TIMELESS", SILENT,
         "Издание 2025 года относит дефект к новой категории.",
         why="«новый» в правиле нет: в корпусе оно значит «только что "
             "созданный», а датированное издание — законная привязка"),
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
    Case("номер записи CVE", "L-RANGE", SILENT,
         "Запись CVE-2007-5277 описывает сброс ограничений при отказе.",
         why="«2007-5277» здесь хвост идентификатора CVE, а не диапазон лет: "
             "слева от числа дефис, значит оно не начинает величину"),
    Case("процент без пробела", "L-PERCENT", CATCH,
         "Доля 20% запросов уходит мимо кеша."),
    Case("неразрывный пробел", "L-NBSP", CATCH,
         "Ответ приходит за 30 мин после запроса.", level="warning"),
    Case("единица «секунда»", "L-NBSP", CATCH,
         "Запрос занял 200 с до ответа.", level="warning"),
    Case("цифра в имени продукта", "L-NBSP", SILENT,
         "Переход на IMDSv2 с отключением первой версии закрывает дефект, "
         "как и разговор по HTTP2 с мультиплексированием.",
         why="«IMDSv2 с» — не «2 с»: слева от числа буква, значит это имя, "
             "а не величина с единицей (находка Н-S4)"),
    Case("предлог «с» после версии и даты", "L-NBSP", SILENT,
         "Проверка Semgrep 1.174.0 с локальным набором правил, тема "
         "прочитана лично 2026-08-25 с комментариями.",
         why="предлог «с», а не секунды: слева от числа точка или дефис, "
             "значит число — хвост версии или даты (заявка З-2)"),
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
    Case("сущность XML в коде", "S-CODE-PUNCT", SILENT,
         "При разборе `&xxe;` парсер читает файл, а `&#38;` даёт амперсанд.",
         why="точка с запятой входит в ссылку на сущность по грамматике "
             "формата: `&xxe` без неё сущностью не является"),
    Case("усечённая запись в коде", "S-CODE-PUNCT", SILENT,
         "Двойное кодирование `%2553...` переживает один проход разбора.",
         why="многоточие показывает, что запись обрезана, и вынести его "
             "наружу кавычек значит соврать про сам код"),
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
    Case("длинное предложение за «Источниками» без номера", "S-SENT-LONG", SILENT,
         "Разбор ниже.\n\n## Источники\n\nБраузер " + words(30) + " дальше.",
         why="хвост аудита не меряется, а у темы-статьи заголовок блока без "
             "номера (переходный режим, решение оператора 2026-10-02)"),
    Case("сокращение не делит предложение", "S-SENT-LONG", CATCH, count=1,
         body="Браузер " + words(14) + ", т. д. и " + words(14) + " дальше.",
         why="точка в «т. д.» не начинает предложение: иначе два коротких "
             "куска вместо одного длинного, и правило промолчит"),
    Case("тире не считается словом", "S-SENT-LONG", SILENT,
         "Сервер " + words(19) + " — путь — сток — дальше.",
         why="счёт по пробелам делал из тире слово, и предложение объявлялось "
             "длинным за пунктуацию, которой свод же и требует (`L-DASH`)"),
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
         why="блок «Источники» — список чужих названий"),
    Case("блок источников без номера", "G-CANON", SILENT,
         "Разбор ниже.\n\n## Источники\n\n- Session — про срок жизни.",
         why="переходный режим (решение оператора 2026-10-02): у темы-статьи "
             "заголовок без номера, блок опознаётся по имени"),
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
    Case("термин в блоке источников", "G-FIRST", SILENT,
         "Разбор ниже.\n\n## 13. Источники\n\n1. `security-headers` — HSTS и соседи.",
         why="блок «Источники» говорит о чужих документах, а не о материале этой"),
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
# функции от `(Page, Ctx)`, правила уровня корпуса — от списка страниц. Базы
# страничных мутаций синтетические (`MODEL_PAGE`, `L3_PAGE`, `REF_PLAN_PAGE`):
# их якоря — строки старой нумерованной формы, а живые темы переписываются в
# статейную форму батчами (до 2026-10-03 базой была живая `password-storage`,
# чья перепись сняла бы полсотни якорей разом). Правила уровня корпуса
# (`C-REF-*`, `C-TAX-*`) по-прежнему смотрят на живой корпус: их предмет —
# сам корпус.


def _fill(paras: int) -> str:
    """Проза-наполнитель блока: норма объёма L1 — от 2500 слов текста (3.1),
    и фикстуре нужен запас, чтобы «внутри нормы» не распадалось от правки
    одного абзаца."""
    sent = ("Пароль проверяется на сервере, и проверка стоит времени, "
            "поэтому цена догадки задаётся в коде.")
    return "\n\n".join([sent] * paras)


# Эталонная тема L1 скелета «уязвимость»: полное frontmatter по схеме и все
# четырнадцать блоков. Собрана по форме настоящей темы (`password-storage`
# в нумерованной форме до роллаута); id оставлен настоящим, потому что лаба
# в `labs.yaml` привязана к теме по `topic`, а фикстура живёт только в /tmp
# и в проверки корпуса не попадает. Дата `reviewed` — всегда сегодня: с
# зафиксированным числом фикстура через `review_interval` месяцев краснела бы
# сама, без чьей-либо ошибки. Страница в /tmp, поэтому норма 6.4 про
# неразрывный пробел между числом и единицей на неё не смотрит.
MODEL_PAGE = f"""---
id: password-storage
plan_id: t-1-6-07
title: 'Хранение паролей: bcrypt, argon2, почему не SHA'
summary: >
  В каком виде пароль лежит в базе, во что обходится атакующему одна догадка
  после утечки дампа и чем цена догадки задаётся в коде.
stage: web-vulns
order: 480
status: published
depth: L1
mode: концепт
time_min: 90
teaches:
  - Объяснить, почему быстрая хеш-функция не годится для хранения пароля
  - Отличить в коде хранение пароля от хеширования высокоэнтропийного секрета
  - Назвать, что даёт соль и чего она не даёт
  - Подобрать параметры scrypt или Argon2id по действующей рекомендации
  - Проверить фикс ретестом и регрессом, не сломав вход старым пользователям
prerequisites: [app-architecture, sessions-vs-tokens]
related: [sessions-vs-tokens, tls-and-proxy]
tags: [auth, crypto]
cwe: [CWE-916, CWE-759, CWE-760, CWE-328]
asvs: ['v5.0-11.4.2', 'v5.0-6.2.1', 'v5.0-6.2.8', 'v5.0-6.2.9', 'v5.0-6.5.2', 'v5.0-7.2.3']
wstg: ['WSTG-v42-CRYP-04']
owasp: ['A07:2025', 'A04:2025']
labs: [lab-password-storage]
sources: [owasp-cs-password-storage, nist-sp-800-63b, wstg-v42-cryp-04-weak-encryption, rfc9106-argon2, python-hashlib, node-crypto]
reviewed: {dt.date.today().isoformat()}
review_interval: 24
---

# Хранение паролей: bcrypt, argon2, почему не SHA

Уровень **L1** · время 90 мин (теория 40 / лаба 35 / самопроверка 15,
оценка)

Что прочитать сначала: `app-architecture`, `sessions-vs-tokens`.

Вот строка из слитой базы:

```text
anna:3fc0a7acf087f549ac2b266baf94b8b1
```

Пароль здесь — `qwerty123`, и узнать это можно без всякого взлома: хеш
вбивается в поисковик, и ответ приходит первой ссылкой.

{_fill(2)}

## 0. Коротко

Пароль в базе хранится не для чтения, а для сравнения с присланным, поэтому
его превращают в необратимое значение с солью и настраиваемой ценой догадки.

**Зачем это в работе AppSec-инженера.** Дефект виден в одной строке кода, и
находка на ревью ставится по имени функции рядом с именем переменной.

{_fill(3)}

## 1. Цели

После этого раздела вы сможете:

1. Объяснить на числах, почему быстрая хеш-функция не годится для пароля.
2. Отличить в коде хранение пароля от хеширования высокоэнтропийного секрета.
3. Назвать, что даёт соль и чего она не даёт.
4. Подобрать параметры scrypt или Argon2id по действующей рекомендации.
5. Проверить фикс ретестом и регрессом, не сломав вход старым пользователям.

## 2. Предвопросы

1. База с паролями утекла целиком. Что меняет соль для атакующего?
2. Функция проверки работает 200 мс вместо микросекунды. Кто платит?
3. Пароль хешируют дважды подряд. Во сколько раз это удорожает перебор?

{_fill(2)}

## 3. Механика

**Откуда это взялось.** Задача звучит как «проверять пароль», а не «знать
пароль», поэтому в таблице хранят необратимое значение.

Дефект относят к CWE-916, CWE-759, CWE-760 и CWE-328.

```python
STORE[login] = hashlib.sha256(password.encode()).hexdigest()
```

{_fill(25)}

## 4. Эксплуатация

{_fill(25)}

## 5. Как выглядит в коде

{_fill(25)}

## 6. Как чинится

{_fill(25)}

## 7. Как проверить фикс

{_fill(25)}

## 8. Как ловится автоматикой

{_fill(25)}

## 9. Ловушка

{_fill(25)}

## 10. Чеклист ревью

1. Verify that пароль хешируется функцией с настраиваемым фактором стоимости.
2. Проверьте, что параметры функции не ниже действующей планки.
3. Проверьте, что умолчания библиотеки проверены явно, а не приняты на веру.
4. Проверьте, что соль уникальна для каждой записи и порождается CSPRNG.
5. Проверьте, что алгоритм и его параметры хранятся вместе с хешем.
6. Проверьте, что результат сравнивается за постоянное время.
7. Проверьте, что пароль проверяется ровно в том виде, в каком пришёл.
8. Проверьте, что для записей старого формата заведён путь миграции.

## 11. Лаба

{_fill(25)}

## 12. Проверь себя

1. В какой из двух функций дефект, если вызовы дословно совпадают?
2. Какую починку вы выберете для регистрации из блока 5?
3. Кто платит двести миллисекунд проверки и сколько раз в секунду?
4. Возврат к теме `sessions-vs-tokens`: чем требования к идентификатору
   сессии отличаются от требований к хранению пароля?
5. Возврат к теме `app-architecture`: куда попадает копия таблицы учётных
   записей, кроме самой базы?

<details markdown="1">
<summary>Ответ 1</summary>

1. Ответ первый.

</details>

<details markdown="1">
<summary>Ответ 2</summary>

2. Ответ второй.

</details>

<details markdown="1">
<summary>Ответ 3</summary>

3. Ответ третий.

</details>

<details markdown="1">
<summary>Ответ 4</summary>

4. Ответ четвёртый.

</details>

<details markdown="1">
<summary>Ответ 5</summary>

5. Ответ пятый.

</details>

## 13. Источники

1. OWASP Password Storage Cheat Sheet; реестр `owasp-cs-password-storage`.
   <https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html>
2. NIST SP 800-63B-4 «Digital Identity Guidelines»; реестр `nist-sp-800-63b`.
   <https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63b-4.pdf>
3. OWASP WSTG-CRYP-04 «Testing for Weak Encryption»; реестр
   `wstg-v42-cryp-04-weak-encryption`.
   <https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/04-Testing_for_Weak_Encryption>
4. RFC 9106 «Argon2 Memory-Hard Function for Password Hashing»; реестр
   `rfc9106-argon2`.
   <https://www.rfc-editor.org/rfc/rfc9106.html>
5. Документация Python, модуль hashlib; реестр `python-hashlib`.
   <https://docs.python.org/3/library/hashlib.html>
6. Документация Node.js, модуль crypto; реестр `node-crypto`.
   <https://nodejs.org/api/crypto.html>

Каркас этапа: `owasp-asvs-5-document` (ASVS v5.0.0), `owasp-wstg-42`,
`owasp-top10-2025`. Наследуются всеми темами и отдельной строкой не
повторяются.

**Скоропортящийся слой.** Параметры функций и число итераций привязаны к
железу и пересматриваются с каждой ревизией.

**Маркеры уверенности.** Параметры и требования проверены по документации.
"""
# База для `C-HEAD-L3-SELFCHECK` — синтетическая тема L3, а не живая страница:
# правилу нужна шапка старой формы «Уровень … · время N мин», а живые темы
# переписываются в статейную форму батчами, и этой строки в них уже нет.
# (До 2026-10-03 базой была живая `dom-clobbering`; её перепись сняла якорь,
# и мутация перестала применяться.) Страница живёт в /tmp, поэтому норма 6.4
# про неразрывный пробел между числом и единицей на неё не смотрит.
L3_PAGE = """---
id: fx-l3-head
title: 'Фикстура шапки L3'
stage: web-vulns
order: 9990
status: published
depth: L3
mode: концепт
time_min: 12
---

# Фикстура шапки L3

Уровень **L3** · время 12 мин

## 3. Механика

Текст механики.
"""

# Страница для `C-REF-PLAN`: фраза со ссылкой на подраздел плана. «1.4» —
# написанный подраздел («XSS и клиентские уязвимости»), «1.99» в плане нет.
# Синтетика по той же причине: ссылка живёт в прозе, а живая проза корпуса
# переписывается (до 2026-10-03 мутация адресовалась к строке `cookies`).
REF_PLAN_PAGE = """---
id: fx-ref-plan
---

# Фикстура ссылки на план

Смежный дефект разобран в подразделе 1.4 плана.
"""


class Nothing:
    """Заглушка для фикстуры, чья мутация не применилась."""

    rule = "МУТАЦИЯ-НЕ-ПРИМЕНИЛАСЬ"
    level = "error"


def model_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — контентная модель на мутациях темы."""
    ctx = vc.Ctx()
    base = MODEL_PAGE
    # Дата ревизии берётся из самой фикстуры, а не пишется здесь числом:
    # фикстура собрана с сегодняшней датой, и мутации про `reviewed` применяются
    # всегда; будущая дата для `C-FM-DATE` тоже считается от сегодня, а не
    # зафиксирована — иначе обе мутации со временем перестали бы ловить.
    seen = re.search(r"(?m)^reviewed: (\d{4}-\d\d-\d\d)$", base)
    assert seen, "MODEL_PAGE: нет поля reviewed — мутации не построить"
    REV = seen.group(1)
    FUT = (dt.date.today() + dt.timedelta(days=400)).isoformat()
    # Каталог этапа сохраняется: иначе C-FM-STAGE-DIR сработает на каждой
    # фикстуре и утонет в выводе всё остальное. Имя файла повторяет `id`:
    # `C-FM-ID` требует, чтобы они совпадали.
    home = tmp / "model" / ctx.stages["web-vulns"]["dir"]
    home.mkdir(parents=True, exist_ok=True)
    target = home / "password-storage.md"

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
        """Мутация по выражению: перестановка полей с группой литералом не
        пишется, а приписывание следа к шапке выражением короче."""
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

    def taxonomy(mutate) -> list:
        """Замечания уровня словаря: `code_categories` подменён, темы живые."""
        alt = copy.copy(ctx)
        alt.categories = {k: dict(v) if isinstance(v, dict) else v
                          for k, v in ctx.categories.items()}
        mutate(alt.categories)
        return vc.check_taxonomy(vc.load_pages(), alt)

    def elsewhere() -> list:
        """Та же тема, но в каталоге другого этапа."""
        alien = tmp / "model" / ctx.stages["appsec-tooling"]["dir"]
        alien.mkdir(parents=True, exist_ok=True)
        dest = alien / "password-storage.md"
        dest.write_text(base, encoding="utf-8")
        return vc.check_front(vc.read_page(dest), ctx)

    def downgraded() -> list:
        """L1-тема, объявленная L2: блоки 2, 7 и 8 на L2 не предусмотрены."""
        return one(base.replace("depth: L1", "depth: L2")
                       .replace("Уровень **L1**", "Уровень **L2**"))

    def corpus_synth(old_text: str, new_text: str) -> list:
        """Мутация прозы синтетической страницы рядом с живым корпусом.

        Ссылки на план живут в тексте, не в полях, поэтому страница с нужной
        фразой (`REF_PLAN_PAGE`) добавляется к загруженному корпусу уже
        мутированной; остальные страницы живые. Замечание-сирота о новой
        странице отсекается вердиктом: проверяется только `C-REF-PLAN`.
        """
        if old_text not in REF_PLAN_PAGE:
            return [Nothing()]
        pages = vc.load_pages()
        target_page = home / "fx-ref-plan.md"
        target_page.write_text(REF_PLAN_PAGE.replace(old_text, new_text, 1),
                               encoding="utf-8")
        pages.append(vc.read_page(target_page))
        return vc.check_refs(pages, ctx)

    def swap_blocks(first: str, second: str) -> list:
        """Поменять два блока местами, сохранив их содержимое."""
        ia, ib = base.find(first), base.find(second)
        end = base.find("\n## ", ib + 1)
        return one(base[:ia] + base[ib:end] + base[ia:ib] + base[end:])

    # Та же фикстура, но L3: каталог этапа тот же (stage-1 → web-vulns),
    # поэтому `home` подходит без нового пути.
    l3base = L3_PAGE
    l3target = home / "fx-l3-head.md"

    def one_l3(text: str) -> list:
        if text == l3base:
            return [Nothing()]
        l3target.write_text(text, encoding="utf-8")
        page = vc.read_page(l3target)
        return (vc.check_front(page, ctx) + vc.check_head(page, ctx)
                + vc.check_blocks(page, ctx) + vc.check_body(page, ctx))

    clean_l3 = one_l3(l3base + "\n")
    clean = one(base + "\n")

    # Тема-статья (решение оператора 2026-10-02): номера заголовков сняты,
    # строки «Уровень …» и «Что прочитать сначала» убраны — их данные живут во
    # frontmatter. Шапка снимается выражением, потому что она двухстрочная.
    art = re.sub(r"(?m)^## \d+\. ", "## ", base)
    art = re.sub(r"Уровень \*\*L1\*\*[^\n]*\nоценка\)\n\n", "", art)
    art = art.replace(
        "Что прочитать сначала: `app-architecture`, `sessions-vs-tokens`.\n\n",
        "", 1)
    art_no_fix = (art[:art.index("## Как чинится")]
                  + art[art.index("## Как проверить фикс"):])
    art_l3 = art.replace("depth: L1", "depth: L3")
    art_dup = art.replace("## Источники", "## Ловушка\n\nТекст.\n\n## Источники", 1)
    out = [
        # тема-фикстура проверки проходит: без этого все «ловит» ниже ничего не
        # доказывают — они могли бы срабатывать на самом тексте
        ("тема-фикстура L1 целиком", ANY, SILENT, clean),

        # --- frontmatter -----------------------------------------------------
        ("нет обязательного поля", "C-FM-REQUIRED", CATCH,
         sub("mode: концепт\n", "")),
        ("поле вне схемы", "C-FM-UNKNOWN", CATCH,
         sub("order: 480\n", "order: 480\nnext: [x]\n")),
        ("поля не в порядке схемы", "C-FM-SEQ", CATCH,
         sub_re(r"status: (draft|published)\ndepth: L1",
                r"depth: L1\nstatus: \1")),
        ("условные поля на своём месте", "C-FM-SEQ", SILENT,
         sub(f"reviewed: {REV}\nreview_interval",
             f"derived_from: [python-hashlib]\nupdated: {REV}\n"
             f"reviewed: {REV}\nreview_interval", 1),
         "`derived_from` и `updated` — условные поля 9.3 и 9.6 п. 19"),
        ("маркер «можно отложить» на своём месте", ANY, SILENT,
         sub("related: [sessions-vs-tokens, tls-and-proxy]\ntags:",
             "related: [sessions-vs-tokens, tls-and-proxy]\n"
             "skip_if: 'пароли в базе не храните: вход через SSO'\ntags:"),
         "`skip_if` — необязательная строка между `related` и `fixes_in` "
         "(`SCHEMA.md` § 3, решение оператора 2026-10-01): ни неизвестного "
         "поля, ни сбоя порядка, ни замечания о типе быть не должно"),
        ("маркер «можно отложить» не строкой", "C-FM-TYPE", CATCH,
         sub("related: [sessions-vs-tokens, tls-and-proxy]\ntags:",
             "related: [sessions-vs-tokens, tls-and-proxy]\n"
             "skip_if: [sso, mfa]\ntags:")),
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
             f"reviewed: {FUT}\nreview_interval", 1)),
        ("reviewed в будущем", "C-FM-DATE", CATCH,
         sub(f"reviewed: {REV}\nreview_interval",
             f"reviewed: {FUT}\nreview_interval", 1)),
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
        # Шапка после чистки 2026-08-24 несёт уровень, время и — отдельным
        # абзацем — предпосылки. Код темы, `reviewed:`, «проверено на:» и
        # маппинг со страницы убраны; на их возвращение стоит `C-HEAD-CLEAN`.
        ("уровень в шапке другой", "C-HEAD-DEPTH", CATCH,
         sub("Уровень **L1**", "Уровень **L2**")),
        ("время в шапке другое", "C-HEAD-TIME", CATCH,
         sub_re(r"время 90(\s)мин", r"время 95\1мин")),
        ("слагаемые времени не дают суммы", "C-HEAD-TIME", CATCH,
         sub("(теория 40 / лаба 35", "(теория 40 / лаба 30")),
        ("предпосылки на странице другие", "C-HEAD-PREREQ", CATCH,
         sub("Что прочитать сначала: `app-architecture`, `sessions-vs-tokens`.",
             "Что прочитать сначала: `app-architecture`.")),
        ("предпосылок нет, а абзац есть", "C-HEAD-PREREQ", CATCH,
         sub("prerequisites: [app-architecture, sessions-vs-tokens]",
             "prerequisites: []", 1)),
        ("код темы вернулся в шапку", "C-HEAD-CLEAN", CATCH,
         sub("Уровень **L1**", "**AG-AUTH-07** · уровень **L1**")),
        ("дата ревизии вернулась в шапку", "C-HEAD-CLEAN", CATCH,
         sub_re(r"(время 90.мин)", r"\1 · reviewed: 2026-08-23")),
        ("«проверено на» вернулось в шапку", "C-HEAD-CLEAN", CATCH,
         sub_re(r"(время 90.мин)", r"\1 · проверено на: Python 3.14.7")),
        ("маппинг вернулся в шапку", "C-HEAD-CLEAN", CATCH,
         sub_re(r"(время 90.мин)", r"\1 · маппинг: CWE-916")),
        ("декларация состава вернулась", "C-HEAD-CLEAN", CATCH,
         sub("Что прочитать сначала:",
             "Состав блоков — полный по уровню L1. Что прочитать сначала:")),
        # Разбивка времени с «самопроверкой» на L3 обещает блок, которого на
        # этом уровне нет (аудит 2026-09: девять таких шапок, гейт был слеп).
        # Слагаемые подобраны в сумму `time_min`, чтобы мутация задевала ровно
        # одно правило, а не `C-HEAD-TIME` заодно.
        ("шапка L3 обещает самопроверку", "C-HEAD-L3-SELFCHECK", CATCH,
         one_l3(re.sub(r"(время \d+.мин)",
                       r"\1 (теория 7 / задача 3 / самопроверка 2)", l3base))),
        ("шапка L3 без разбивки", "C-HEAD-L3-SELFCHECK", SILENT, clean_l3,
         "на L3 разбивки нет вовсе — обещать самопроверку нечему"),
        ("разбивка с самопроверкой на L1", "C-HEAD-L3-SELFCHECK", SILENT, clean,
         "на L1–L2 разбивка обязательна: правило спрашивается только с L3"),

        # --- скелет ----------------------------------------------------------
        ("блок назван не по канону", "C-BLOCK-TITLE", CATCH,
         sub("## 9. Ловушка", "## 9. Западня")),
        ("блоки переставлены", "C-BLOCK-ORDER", CATCH,
         swap_blocks("## 9. Ловушка", "## 10. Чеклист ревью")),
        ("нет обязательного блока", "C-BLOCK-REQ", CATCH,
         cut("## 7. Как проверить фикс", "## 8. Как ловится")),
        ("заголовок блока не нумерован", "C-BLOCK-SHAPE", CATCH,
         sub("## 9. Ловушка", "## Ловушка")),
        ("номер блока вне скелета", "C-BLOCK-NUM", CATCH,
         sub("## 9. Ловушка", "## 19. Ловушка")),

        # --- переходный режим: тема-статья (решение оператора 2026-10-02) -----
        # Та же тема без номеров заголовков: блоки распознаются по имени
        # (старому или живому из `LIVE_TITLES`), строка «Уровень … · время …»
        # и абзац «Что прочитать сначала» опциональны, «Коротко» и «Цели»
        # необязательны, свободные разделы законны, порядок не проверяется.
        # Обязательность остального и предусмотренность уровнем сохранены.
        ("статья: номера сняты, шапка на месте", ANY, SILENT,
         one(re.sub(r"(?m)^## \d+\. ", "## ", base)),
         "обе формы законны; шапка в статье не запрещена, а сверяется"),
        ("статья: без номеров, шапки и предпосылок", ANY, SILENT, one(art),
         "форма эталона новой подачи — пилота `tls-and-proxy` этапа 0"),
        ("у статьи пропал обязательный блок", "C-BLOCK-REQ", CATCH,
         one(art_no_fix)),
        ("у статьи блок не по уровню", "C-BLOCK-EXTRA", CATCH, one(art_l3)),
        ("в статье блок повторился", "C-BLOCK-ORDER", CATCH, one(art_dup)),
        ("в статье живое имя блока", ANY, SILENT,
         one(art.replace("## Механика", "## Как это работает", 1)),
         "старое и живое имя равнозаконны: «Механика» ↔ «Как это работает»"),

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
        ("пункт чеклиста не в залоге", "C-BODY-CHECKLIST", SILENT,
         sub("1. Verify that", "1. Убедитесь, что", 1),
         "формула «Verify that…» снята решением оператора 2026-10-01 (RN-10): "
         "машина следит за числом пунктов, залог — дело автора"),
        ("нет ответов под раскрытием", "C-BODY-SELFCHECK", CATCH,
         sub("<details", "<detailz")),
        # Возврат целит любую более раннюю тему маршрута (правило 35
        # research/09, решение оператора 2026-10-01). Ошибка — цель позже по
        # маршруту или вне корпуса: `sast-principles` стоит этапом позже
        # настоящей темы.
        ("возврат ведёт на более позднюю тему", "C-BODY-RETURN", CATCH,
         sub("Возврат к теме `sessions-vs-tokens`",
             "Возврат к теме `sast-principles`", 1)),
        ("возврат ведёт в никуда", "C-BODY-RETURN", CATCH,
         sub("Возврат к теме `sessions-vs-tokens`",
             "Возврат к теме `net-takoy-temy`", 1)),
        ("возврат ведёт на раннюю тему вне предпосылок", "C-BODY-RETURN", SILENT,
         sub("Возврат к теме `sessions-vs-tokens`",
             "Возврат к теме `http-basics`", 1),
         "правило 35: законна любая тема раньше по маршруту, не только "
         "предпосылка"),
        ("возврат ведёт на предпосылку", "C-BODY-RETURN", SILENT, clean,
         "предпосылки стоят раньше по маршруту — законные цели (правило 35)"),
        ("сноска и sources расходятся", "C-BODY-SOURCES", CATCH,
         sub("`python-hashlib`", "`mdn-csp`")),
        ("каркас этапа не в sources", "C-BODY-SOURCES", SILENT, clean,
         "источники этапа названы прозой после сносок и в `sources` не дублируются"),
        ("идентификатор в тексте не объявлен", "C-BODY-IDENT", CATCH,
         sub("cwe: [CWE-916, CWE-759, CWE-760, CWE-328]",
             "cwe: [CWE-916, CWE-759, CWE-328]", 1)),
        ("идентификатор объявлен и не напечатан", "C-BODY-IDENT", SILENT,
         sub("wstg: ['WSTG-v42-CRYP-04']", "wstg: ['WSTG-v42-CRYP-04', "
             "'WSTG-v42-CRYP-01']", 1),
         "маппинг со страницы убран: ненапечатанный номер — норма, а не дефект"),

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
         corpus_synth("в подразделе 1.4", "в подразделе 1.99")),
        # --- словари против плана: C-TAX-* -----------------------------------
        ("категория на подраздел вне плана", "C-TAX-CATEGORY", CATCH,
         taxonomy(lambda c: c.__setitem__("INJ", {"sub": "1.99", "means": "х"}))),
        ("две категории на один подраздел", "C-TAX-CATEGORY", CATCH,
         taxonomy(lambda c: c.__setitem__("DUP", {"sub": "1.3", "means": "х"}))),
        ("написанный подраздел без категории", "C-TAX-CATEGORY", CATCH,
         taxonomy(lambda c: c.pop("INJ"))),
        ("категория без номера подраздела", "C-TAX-CATEGORY", CATCH,
         taxonomy(lambda c: c.__setitem__("INJ", "одной строкой"))),
        ("живой словарь сходится с планом", "C-TAX-CATEGORY", SILENT,
         taxonomy(lambda c: None),
         "у каждого написанного подраздела ровно одна категория"),

        # Сирота делается из темы, на которую входящих ссылок не остаётся после
        # мутации: `corpus` правит только frontmatter. С 2026-08-31 входящие —
        # только смысловые рёбра (`prerequisites`, `related`, `fixes_in`): ребра
        # из блока «Дальше» ушли вместе с блоком, ссылку вперёд генерирует
        # сборка. История фикстуры: она зеленела не своей мутацией, а настоящей
        # сиротой корпуса — `password-storage`, у которой входящих не было
        # вовсе. Как только сироту закрыли, обман вскрылся: правило молчало,
        # а утверждение считалось выполненным.
        ("тема без входящих ссылок", "C-REF-ORPHAN", CATCH,
         corpus(lambda d: [p.front.__setitem__(
             "prerequisites", [x for x in p.front.get("prerequisites") or []
                               if x != "access-control-models"])
             or p.front.__setitem__(
                 "related", [x for x in p.front.get("related") or []
                             if x != "access-control-models"])
             for p in d.values()])),
        ("настоящий корпус: сирот нет", "C-REF-ORPHAN", SILENT,
         corpus(lambda d: None),
         "на каждую тему ссылается хотя бы одна другая"),
    ]
    return out


# ── объём: правила C-VOL-* ───────────────────────────────────────────────────
#
# Весь смысл фикстур — в том, что метод свода 3.1 отбрасывает именно служебный
# аппарат и ничего кроме. База — та же синтетическая `MODEL_PAGE`: норма L1
# (от 2500 слов текста) набрана наполнителем `_fill`, а аппарат (шапка, врезки
# «Зачем это в работе» и «Откуда это взялось», блок «Источники» с хвостом)
# воспроизведён дословно, потому что проверяется именно его выпадение из
# метрики. Верхнего предела нет с 2026-10-02 (решение оператора: статейная
# подача структурно длиннее), поэтому «ловит» проверяется на нижнем пределе
# (`C-VOL-UNDER`), а «аппарат не считается» — на метрике напрямую: приём
# прежний, «дописал — ничего не сдвинулось», только сверяется не вердикт, а
# число слов метрики «текст» до и после дописки.


class Rec:
    """Замечание `wordcount.py` в виде объекта: селф-тест читает `.rule`."""

    def __init__(self, d: dict):
        self.rule, self.level = d["rule"], d["level"]


def volume_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — объём на мутациях темы-фикстуры."""
    base = MODEL_PAGE
    home = tmp / "volume"
    home.mkdir(parents=True, exist_ok=True)
    target = home / "password-storage.md"

    def one(text: str) -> list:
        target.write_text(text, encoding="utf-8")
        return [Rec(d) for d in wcnt.check(target)[2]]

    def sub(old_text: str, new_text: str, count: int = -1) -> list:
        return one(base.replace(old_text, new_text)
                   if count < 0 else base.replace(old_text, new_text, count))

    # Абзац настоящими словами, повторённый с запасом: фикстура не должна
    # ломаться от того, что тема подросла на сотню слов.
    para = ("Пароль проверяется на сервере, и проверка стоит времени. " * 4).strip()
    here = wcnt.counts(base)[2]
    times = 30
    grow = "\n\n".join([para] * times)

    def same_text(mutated: str) -> list:
        """Метрика «текст» не сдвинулась от дописки; иначе синтетический
        провал: аппарат начал считаться, а это дефект метода 3.1. Правило
        C-VOL-METRIC существует только здесь, в самопроверке."""
        return [] if wcnt.counts(mutated)[2] == here else [
            Rec({"rule": "C-VOL-METRIC", "level": "error"})]

    short = base[: base.find("## 3.")] + "## 13. Источники\n"
    return [
        ("тема-фикстура L1 внутри нормы", "C-VOL-UNDER", SILENT, one(base),
         f"{here} слов текста при норме «от {wcnt.NORM['L1']}»"),
        ("уровень темы распознан", "C-VOL-DEPTH", SILENT, one(base)),
        ("верхнего предела объёма нет", "C-VOL-OVER", SILENT,
         sub("## 13.", grow + "\n\n## 13.", 1),
         f"решение оператора 2026-10-02: дописка на {times * 36} слов сверх "
         "прежнего верха нормы 2500–3500 ошибкой больше не является"),
        ("тема ниже нормы уровня", "C-VOL-UNDER", CATCH, one(short)),
        ("уровень не из словаря", "C-VOL-DEPTH", CATCH, sub("depth: L1", "depth: L9")),
        # Служебный аппарат: каждая его часть обязана выпадать из метрики.
        ("блок «Источники» и всё за ним не считаются", "C-VOL-METRIC", SILENT,
         same_text(base.replace("## 13.", "## 13. Источники\n\n" + grow
                                + "\n\n## 13.", 1)),
         f"приписка на {times * 36} слов за блоком «Источники» не сдвигает метрику"),
        ("блок «Источники» без номера тоже отрезает хвост", "C-VOL-METRIC", SILENT,
         same_text(base.replace("## 13. Источники", "## Источники", 1)),
         "переходный режим (решение оператора 2026-10-02): у темы-статьи "
         "заголовок без номера, и хвост режется по имени"),
        ("листинг не считается", "C-VOL-METRIC", SILENT,
         same_text(base.replace("## 13. Источники", "```text\n" + grow
                                + "\n```\n\n## 13. Источники", 1)),
         "листинг того же объёма не сдвигает метрику"),
        # Блок идентификации (шапка «Уровень … · время …» под заголовком)
        # кончается первой пустой строкой, поэтому дописка в него идёт одним
        # абзацем: с пустой строкой внутри это была бы уже проза. Якорь —
        # начало шапки: код темы `**AG-…**`, которым шапка когда-то
        # открывалась, со страниц убран чисткой 2026-08-24.
        ("блок идентификации не считается", "C-VOL-METRIC", SILENT,
         same_text(base.replace("Уровень **L1**", "Уровень **L1** "
                                + " ".join([para] * times), 1)),
         "дописанное в шапку под заголовком выпадает вместе с ней"),
        # Свод 3.1 п. 8 (решение оператора от 2026-08-23): два обязательных
        # абзаца в норму не входят. Проверяется тем же приёмом — абзац растёт,
        # метрика стоит на месте.
        ("абзац «Зачем это в работе» не считается", "C-VOL-METRIC", SILENT,
         same_text(base.replace("**Зачем это в работе AppSec-инженера.**",
                                "**Зачем это в работе AppSec-инженера.** "
                                + " ".join([para] * times), 1)),
         "дописанное во врезку «Зачем это в работе» выпадает вместе с ней"),
        ("абзац «Откуда это взялось» не считается", "C-VOL-METRIC", SILENT,
         same_text(base.replace("**Откуда это взялось.**",
                                "**Откуда это взялось.** "
                                + " ".join([para] * times), 1)),
         "дописанное во врезку «Откуда это взялось» выпадает вместе с ней")]


# ── ссылки: правила S-LINK-* и S-EXT-IN-BODY ─────────────────────────────────
#
# Тот же приём, что у контентной модели: мутируется одно место. База здесь
# синтетическая: мутациям нужна старая нумерованная форма («## 3. Механика»,
# строка «Уровень … · время …», «## 13. Источники»), а живые темы
# переписываются в статейную форму батчами. (До 2026-10-03 базой был живой
# `cookies`; его перепись сняла якоря, и пять мутаций перестали применяться.)
# У фикстуры есть и ссылка на тему в прозе («Возврат к теме `http-basics`»),
# и сноска с автоссылкой в блоке «Источники» — все проверяемые формы сразу.
# На живой странице оставлен один сторож — «настоящая тема целиком»: она чиста
# под всеми четырьмя правилами в любой из двух форм подачи.

BASE_LINK_PAGE = CONTENT_DIR / "stage-0" / "cookies.md"

LINK_PAGE = """---
id: fx-links
title: 'Фикстура ссылок'
stage: protocol-basics
order: 9990
status: published
depth: L2
mode: концепт
time_min: 20
---

# Фикстура ссылок

Уровень **L2** · время 20 мин (теория 12 / задача 8)

## 3. Механика

Ответ сервера несёт заголовок `Set-Cookie`: браузер запоминает пару
«имя-значение» и возвращает её с каждым запросом на свой домен.
Возврат к теме `http-basics`: там разобран сам заголовок.

## 13. Источники

1. «Using HTTP cookies», MDN Web Docs; реестр `mdn-cookies`.
   <https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies>
"""


def link_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — ссылки на мутациях темы-фикстуры."""
    base = LINK_PAGE
    ids = lc.load_ids([])
    source_urls = lc.load_source_urls()
    home = tmp / "links"
    home.mkdir(parents=True, exist_ok=True)
    target = home / "fx-links.md"

    def run(path: Path) -> list:
        doc = mdtext.load(path)
        marks = lc.blocks_of(doc)
        return (lc.check_external_placement(path, doc, marks)
                + lc.check_source_urls(path, doc, marks, source_urls)
                + lc.check_topic_refs(path, doc, ids)
                + lc.check_md_links(path, doc, ids))

    def one(text: str) -> list:
        if text == base:
            return [Nothing()]
        target.write_text(text, encoding="utf-8")
        return run(target)

    def live() -> list:
        """Живая страница корпуса: правила обязаны молчать на настоящем тексте."""
        path = home / BASE_LINK_PAGE.name
        path.write_text(BASE_LINK_PAGE.read_text(encoding="utf-8"),
                        encoding="utf-8")
        return run(path)

    def sub(old_text: str, new_text: str, count: int = -1) -> list:
        return one(base.replace(old_text, new_text)
                   if count < 0 else base.replace(old_text, new_text, count))

    def after_head(added: str) -> list:
        """Вставить текст в блок 3 «Механика» — середина материала темы."""
        return sub("## 3. Механика", "## 3. Механика\n\n" + added + "\n", 1)

    mdn = "<https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies>"
    out = [
        ("тема-фикстура целиком", ANY, SILENT, one(base + "\n"),
         "исходная фикстура чиста под всеми четырьмя правилами: мутации ниже "
         "портят ровно одно место"),
        ("адрес в блоке 3", "S-EXT-IN-BODY", CATCH,
         after_head("Подробности — <https://example.org/spec>.")),
        ("адрес в шапке", "S-EXT-IN-BODY", CATCH,
         sub("Уровень **L2**", "<https://example.org/x> Уровень **L2**", 1)),
        ("адрес в блоке «Источники»", "S-EXT-IN-BODY", SILENT, one(base + "\n"),
         "автоссылка фикстуры стоит там, где ей можно"),
        ("адрес в блоке «Источники» без номера", "S-EXT-IN-BODY", SILENT,
         sub("## 13. Источники", "## Источники", 1),
         "переходный режим (решение оператора 2026-10-02): номер заголовка "
         "опционален, блок опознаётся по имени"),
        ("адрес примером в коде", "S-EXT-IN-BODY", SILENT,
         after_head("Например, `https://evil.com/a` в поле."),
         "инлайновый код — не ссылка"),

        ("сноска без угловых скобок", "S-LINK-BARE", CATCH,
         sub(mdn, mdn[1:-1], 1)),
        ("адрес в обратных кавычках", "S-LINK-BARE", SILENT,
         after_head("Пример: `https://evil.com/a`."),
         "в коде адрес ссылкой и не должен становиться"),

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
         one(base + "\n"), "адрес сноски и `url` реестровой записи совпадают"),

        ("настоящая тема целиком", ANY, SILENT, live(),
         "живая страница корпуса чиста под всеми четырьмя правилами — сторож "
         "на настоящем тексте, в любой из двух форм подачи"),
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


class WrongSkeleton:
    """Заглушка: шаблон лежит под чужим скелетом.

    Без неё шаблон инструмента, забывший поле `skeleton`, прошёл бы как
    «тема начинается зелёной»: скелет по умолчанию — `уязвимость`, и все
    проверки состава спросили бы с него не то.
    """

    rule = "СКЕЛЕТ-НЕ-ТОТ"
    level = "error"


# Имя файла шаблона по скелету: у каждого скелета свода 4.2 своя тройка. Если
# скелет заведён в словаре, а шаблона к нему нет, `template_cases` печатает
# «ШАБЛОНА-НЕТ» — автор новой темы иначе узнал бы об этом на пустом месте.
TEMPLATE_NAME = {"уязвимость": "{depth}.md", "инструмент": "tool-{depth}.md"}


def template_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — шаблоны обоих скелетов, L1, L2, L3."""
    ctx = vc.Ctx()
    staging = tmp / "tpl-raw"
    staging.mkdir(parents=True, exist_ok=True)
    out: list[tuple[str, str, str, list]] = []
    pairs = [(skeleton, depth) for skeleton in sorted(ctx.skeletons)
             for depth in sorted(ctx.depths)]
    for skeleton, depth in pairs:
        pattern = TEMPLATE_NAME.get(skeleton, "{depth}.md")
        src = TEMPLATES_DIR / pattern.format(depth=depth)
        name = f"шаблон {skeleton} {depth}"
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
        if ctx.skeleton_of(page) != skeleton:
            found.append(WrongSkeleton())
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



# ── второй скелет: правила C-FM-SKELETON, C-BODY-FIX, C-BODY-MECH ────────────
#
# Скелетов в своде 4.2 два, и главное требование к проверке — не «пропустить
# оба», а различать их: скелет, который разрешает всё, хуже прежнего, потому
# что тогда пропадает единственная машинная защита от халтуры. Фикстуры ниже
# проверяют ровно это. Базой берутся шаблоны — живой темы-инструмента в корпусе
# ещё нет, а шаблон прогоняется теми же функциями и в `template_cases` уже
# объявлен зелёным.

TOOL_BASE = TEMPLATES_DIR / "tool-L1.md"
TOOL_RECIPE = TEMPLATES_DIR / "tool-L2.md"
VULN_BASE = TEMPLATES_DIR / "L1.md"


def skeleton_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — различение двух скелетов."""
    ctx = vc.Ctx()
    home = tmp / "skel" / ctx.stages["appsec-tooling"]["dir"]
    home.mkdir(parents=True, exist_ok=True)
    vuln_home = tmp / "skel" / ctx.stages["web-vulns"]["dir"]
    vuln_home.mkdir(parents=True, exist_ok=True)

    def one(text: str, base: Path, where: Path) -> list:
        if text == base.read_text(encoding="utf-8"):
            return [Nothing()]
        target = where / "new-topic.md"
        target.write_text(text, encoding="utf-8")
        page = vc.read_page(target)
        return (vc.check_front(page, ctx) + vc.check_head(page, ctx)
                + vc.check_blocks(page, ctx) + vc.check_body(page, ctx))

    def skeletons(mutate) -> list:
        """Замечания уровня словаря: `skeletons` подменён, темы живые."""
        alt = copy.copy(ctx)
        alt.skeletons = {name: {n: dict(b) for n, b in blocks.items()}
                         for name, blocks in ctx.skeletons.items()}
        alt.default_skeleton = ctx.default_skeleton
        mutate(alt)
        return vc.check_skeletons(alt)

    tool = TOOL_BASE.read_text(encoding="utf-8")
    recipe = TOOL_RECIPE.read_text(encoding="utf-8")
    vuln = VULN_BASE.read_text(encoding="utf-8")

    def sub(old_text: str, new_text: str, count: int = -1) -> list:
        return one(tool.replace(old_text, new_text) if count < 0
                   else tool.replace(old_text, new_text, count), TOOL_BASE, home)

    def sub_recipe(old_text: str, new_text: str) -> list:
        return one(recipe.replace(old_text, new_text), TOOL_RECIPE, home)

    def sub_vuln(old_text: str, new_text: str) -> list:
        return one(vuln.replace(old_text, new_text), VULN_BASE, vuln_home)

    def cut(start: str, stop: str) -> list:
        i, j = tool.find(start), tool.find(stop)
        return one(tool if i < 0 or j < i else tool[:i] + tool[j:], TOOL_BASE, home)

    return [
        # --- подмена скелета -------------------------------------------------
        # Самая дорогая ошибка: тема про инструмент, не объявившая себя такой,
        # получает состав темы-уязвимости и обязана нести «Как чинится».
        ("тема-инструмент не объявила скелет", "C-BLOCK-TITLE", CATCH,
         sub("skeleton: инструмент\n", "")),
        ("скелет вне словаря", "C-FM-VOCAB", CATCH,
         sub("skeleton: инструмент", "skeleton: инструментальный")),
        ("блок чужого скелета на странице", "C-BLOCK-TITLE", CATCH,
         sub("## 6. Как читать вывод", "## 6. Как чинится")),
        ("нет блока, обязательного у инструмента", "C-BLOCK-REQ", CATCH,
         cut("## 7. Границы метода", "## 8. Ловушка")),
        ("номер блока вне скелета инструмента", "C-BLOCK-NUM", CATCH,
         sub("## 8. Ловушка", "## 14. Ловушка")),
        # Спуск L2 до L3 сразу даёт девять блоков, которых уровень не несёт.
        ("блок не по уровню в скелете инструмента", "C-BLOCK-EXTRA", CATCH,
         one(recipe.replace("depth: L2", "depth: L3")
                   .replace("Уровень **L2**", "Уровень **L3**"),
             TOOL_RECIPE, home)),

        # --- связь вместо блока «Как чинится» --------------------------------
        ("тема-инструмент без `fixes_in`", "C-FM-SKELETON", CATCH,
         sub("fixes_in: [sqli-basics]\n", "")),
        ("`fixes_in` пуст при названном классе дефекта", "C-FM-SKELETON", CATCH,
         sub("fixes_in: [sqli-basics]", "fixes_in: []")),
        ("`fixes_in` у темы-уязвимости", "C-FM-SKELETON", CATCH,
         sub_vuln("related: [cookies, sessions-vs-tokens]",
                  "related: [cookies, sessions-vs-tokens]\nfixes_in: [cookies]")),
        ("связь названа только в шапке", "C-BODY-FIX", CATCH,
         sub("`sqli-basics`", "`parameterized-queries`")),
        ("`fixes_in` пуст, класс дефекта не назван", "C-FM-SKELETON", SILENT,
         one(tool.replace("fixes_in: [sqli-basics]", "fixes_in: []")
                 .replace("cwe: [CWE-000]", "cwe: []"), TOOL_BASE, home),
         "инструмент, который дефектов не находит, связывать не с чем"),

        # --- словарь скелетов против проверок, которые его читают -------------
        # Ключ пропал — проверка не упала, а выключилась: `C-BODY-SOURCES`
        # промолчит на теме без единой сноски. Это и ловится.
        ("у скелета нет блока с ключом проверки", "C-TAX-SKELETON", CATCH,
         skeletons(lambda c: c.skeletons["инструмент"][12].__setitem__(
             "key", "footnotes"))),
        ("ключ блока повторяется", "C-TAX-SKELETON", CATCH,
         skeletons(lambda c: c.skeletons["инструмент"][11].__setitem__(
             "key", "sources"))),
        ("умолчание указывает на несуществующий скелет", "C-TAX-SKELETON", CATCH,
         skeletons(lambda c: setattr(c, "default_skeleton", "никакой"))),
        ("дыра в нумерации скелета", "C-TAX-SKELETON", CATCH,
         skeletons(lambda c: c.skeletons["инструмент"].pop(8))),
        ("живой словарь скелетов сходится с проверками", "C-TAX-SKELETON", SILENT,
         skeletons(lambda c: None),
         "у обоих скелетов есть все блоки, которые ищут `C-BODY-*`"),

        # --- механика в рецепте ----------------------------------------------
        # Оговорка 9.2: механика в рецепте пишется в объёме, нужном, чтобы
        # понять вывод, а разбор остаётся в своей теме. Машина меряет не объём
        # — метром тут была бы выдуманная граница, — а наличие адреса.
        ("механика рецепта без адреса разбора", "C-BODY-MECH", CATCH,
         sub_recipe("Механизм самого дефекта\nразобран в `sqli-basics` — здесь он "
                    "не пересказывается.",
                    "Механизм самого дефекта здесь не пересказывается.")),
        ("механика концепта без адреса разбора", "C-BODY-MECH", SILENT,
         sub("разобран в `sqli-basics`", "разобран в теме своего этапа"),
         "правило спрашивается с рецепта: концепт механизм и объясняет"),
    ]


# ── синтаксис листингов: правило C-CODE-SYNTAX ───────────────────────────────
#
# Договор STYLE.md § 6: блок, первая строка которого — комментарий со словом
# «ФРАГМЕНТ», проверкой пропускается; блок без маркера обязан компилироваться.
# Прогон прямой, как у `volume_cases`: фикстура пишется в файл и отдаётся
# `lint_code.check_file` вместе с каталогом под временные файлы проверок.


def code_cases(tmp: Path) -> list[tuple[str, str, str, list]]:
    """(имя, правило, режим, найденное) — маркер фрагмента и компиляция."""
    home = tmp / "code"
    home.mkdir(parents=True, exist_ok=True)
    work = home / "work"
    work.mkdir()
    target = home / "fixture.md"

    def one(text: str) -> list:
        target.write_text(text, encoding="utf-8")
        return lcd.check_file(target, work)

    frag = "return 1  # срез из середины функции"
    return [
        ("return на верхнем уровне без маркера", "C-CODE-SYNTAX", CATCH,
         one(fence([frag], "python")),
         "голый ast.parse это место пропускает: ловит именно compile()"),
        ("тот же срез с маркером", "C-CODE-SYNTAX", SILENT,
         one(fence(["# ФРАГМЕНТ — срез, самостоятельно не компилируется",
                    frag], "python")),
         "первая строка — комментарий со словом «ФРАГМЕНТ», блок пропускается"),
        ("самодостаточный листинг python", "C-CODE-SYNTAX", SILENT,
         one(fence(["def pick():", "    return 1"], "python"))),
        ("return на верхнем уровне в javascript", "C-CODE-SYNTAX", CATCH,
         one(fence(["if (x) return 1;"], "javascript")),
         "node --check в режиме модуля запрещает return вне функции"),
        ("битый yaml", "C-CODE-SYNTAX", CATCH,
         one(fence(["key: [1, 2", "other: }"], "yaml"))),
    ]


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
                    + list(link_cases(tmp)) + list(code_cases(tmp))
                    + list(template_cases(tmp)) + list(skeleton_cases(tmp))):
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
