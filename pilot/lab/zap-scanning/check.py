#!/usr/bin/env python3
"""Проверялка задачи чтения: сверяет answers.csv с key.yaml и печатает счёт.

Запуск из каталога лабы:
    ../../../.venv-tools/bin/python check.py

Код возврата 0 — зачтено (совпало не меньше 15 строк из 17), 1 — нет.
Сети не требует, стенд поднимать не нужно.
"""
import csv
import pathlib
import sys

import yaml

PASS = 15
HERE = pathlib.Path(__file__).parent
VERDICTS = {"и", "л", "д", "н"}


def load_answers(path):
    with open(path, encoding="utf-8") as fh:
        lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
    return list(csv.DictReader(lines))


def main():
    key = yaml.safe_load((HERE / "key.yaml").read_text(encoding="utf-8"))["key"]
    answers = load_answers(HERE / "answers.csv")
    if len(answers) != len(key):
        print(f"строк в answers.csv {len(answers)}, ожидалось {len(key)}")
        return 1

    good = 0
    for got, want in zip(answers, key):
        place = f"строка {want['строка']}, правило {want['правило']}"
        if int(got["строка"]) != want["строка"] or got["правило"] != want["правило"]:
            print(f"{place}: строка переставлена или изменена")
            continue
        verdict = (got.get("вердикт") or "").strip()
        sign = (got.get("признак") or "").strip()
        if verdict not in VERDICTS:
            print(f"{place}: вердикт не заполнен или не из набора и/л/д/н")
            continue
        if verdict != want["вердикт"]:
            print(f"{place}: вердикт {verdict}, в разметке {want['вердикт']}")
            continue
        if not sign:
            print(f"{place}: вердикт верный, признак не назван — не засчитано")
            continue
        good += 1

    print(f"\nсовпало {good} из {len(key)}, порог {PASS}")
    if good >= PASS:
        print("зачтено")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
