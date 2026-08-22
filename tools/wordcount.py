"""Подсчёт слов в теме гайда — двумя методами сразу.

    python tools/wordcount.py content/stage-0/*.md

`тело`  — весь текст после frontmatter.
`проза` — тело без листингов, без ответов под <details> и без блока 14.
`текст` — проза без служебного аппарата: строки о составе блоков, описания
          схем, скоропортящегося слоя, маркеров уверенности, каркаса этапа.

Свод (3.1) нормы объёма задаёт, но метода подсчёта не задаёт: расхождение
между колонками и есть цена этого пробела (находка Ф-09 приёмки). Служебный
аппарат предписан 9.6 п. 21, 11.2 п. 12 и частью 4, но в норму 800–1200 слов
не заложен — на темах этапа 0 он стоит около 200 слов.
"""

import re
import sys
from pathlib import Path

FRONT = re.compile(r"\A---\n.*?\n---\n", re.S)
FENCE = re.compile(r"^```.*?^```", re.M | re.S)
DETAILS = re.compile(r"<details>.*?</details>", re.S)
SOURCES = re.compile(r"^## 14\..*\Z", re.M | re.S)
SERVICE = re.compile(
    r"^(?:Состав блоков — |\*\*Описание схемы\.\*\*|\*\*Скоропортящийся слой\.\*\*"
    r"|\*\*Маркеры уверенности\.\*\*|Каркас этапа:).*?(?:\n\n|\Z)",
    re.M | re.S,
)
WORD = re.compile(r"[0-9A-Za-zА-Яа-яЁё][0-9A-Za-zА-Яа-яЁё'’-]*")


def counts(text: str) -> tuple[int, int, int]:
    body = FRONT.sub("", text)
    prose = SOURCES.sub("", DETAILS.sub("", FENCE.sub("", body)))
    core = SERVICE.sub("", prose)
    return (
        len(WORD.findall(body)),
        len(WORD.findall(prose)),
        len(WORD.findall(core)),
    )


def main(argv: list[str]) -> int:
    print(f"{'файл':<34}{'тело':>8}{'проза':>8}{'текст':>8}")
    for name in argv:
        body, prose, core = counts(Path(name).read_text(encoding="utf-8"))
        print(f"{Path(name).name:<34}{body:>8}{prose:>8}{core:>8}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
