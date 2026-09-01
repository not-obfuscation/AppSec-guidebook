#!/usr/bin/env python3
"""Проверялка лабы owasp-asvs.

Сверяет answers.csv с key.yaml: вердикт по каждому требованию обязан
совпасть с эталоном, а признак — быть непустым (вердикт без опоры на
снимок не считается).

Запуск из каталога лабы:  python3 check.py
Код возврата 0 — зачтено, 1 — нет.
"""

import csv
import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).parent


def main():
    key = {r["id"]: r for r in yaml.safe_load(
        (HERE / "key.yaml").read_text("utf-8"))["key"]}
    with open(HERE / "answers.csv", encoding="utf-8") as fh:
        lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
    rows = list(csv.DictReader(lines))
    if len(rows) != len(key):
        print(f"строк {len(rows)}, ожидалось {len(key)}")
        return 1

    ok = True
    for row in rows:
        want = key.get(row["id"])
        if want is None:
            print(f"{row['id']}: требования нет в списке прогона")
            ok = False
            continue
        got = (row.get("verdict") or "").strip()
        if got != want["verdict"]:
            print(f"{row['id']}: вердикт «{got}», эталон "
                  f"«{want['verdict']}» — {want['почему']}")
            ok = False
        if not (row.get("признак") or "").strip():
            print(f"{row['id']}: признак пуст")
            ok = False

    print("зачтено: все шесть вердиктов сошлись и имеют признак"
          if ok else "не зачтено")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
