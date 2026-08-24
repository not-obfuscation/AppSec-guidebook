#!/usr/bin/env python3
"""Проверялка лабы: сверяет answers.csv с key.yaml и печатает счёт.

Запуск из каталога лабы:
    ../../../.venv-tools/bin/python check.py

Код возврата 0 — зачтено (совпало не меньше 14 строк из 15), 1 — нет.
"""
import csv
import pathlib
import sys

import yaml

PASS = 14
HERE = pathlib.Path(__file__).parent
VERDICTS = {"и", "л", "д"}


def load_answers(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
    for row in csv.DictReader(lines):
        rows.append(row)
    return rows


def main():
    key = yaml.safe_load((HERE / "key.yaml").read_text(encoding="utf-8"))["key"]
    answers = load_answers(HERE / "answers.csv")
    if len(answers) != len(key):
        print(f"строк в answers.csv {len(answers)}, ожидалось {len(key)}")
        return 1

    good = 0
    for got, want in zip(answers, key):
        place = f"{want['инструмент']} {want['файл']}:{want['строка']} {want['правило']}"
        same_place = (
            got["инструмент"] == want["инструмент"]
            and got["файл"] == want["файл"]
            and int(got["строка"]) == int(want["строка"])
            and got["правило"] == want["правило"]
        )
        if not same_place:
            print(f"строка переставлена или изменена: ожидалось {place}")
            continue
        verdict = (got.get("вердикт") or "").strip()
        sign = (got.get("признак") or "").strip()
        if verdict not in VERDICTS:
            print(f"{place}: вердикт не заполнен или не из набора и/л/д")
            continue
        if verdict != want["вердикт"]:
            print(f"{place}: вердикт {verdict}, в разметке {want['вердикт']}")
            continue
        if not sign:
            print(f"{place}: вердикт верный, признак не назван — не засчитано")
            continue
        good += 1

    print(f"\nсовпало {good} из {len(key)}, порог {PASS}")
    return 0 if good >= PASS else 1


if __name__ == "__main__":
    sys.exit(main())
