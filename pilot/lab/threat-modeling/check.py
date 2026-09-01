#!/usr/bin/env python3
"""Проверялка лабы threat-modeling.

Сверяет answers.csv с key.yaml по шести элементам учебной витрины:
тип элемента и граница доверия должны совпасть с эталоном, категория
STRIDE — тоже, а формулировка угрозы обязана быть непустой (она своя).

Запуск из каталога лабы:  python3 check.py
Код возврата 0 — зачтено, 1 — нет.
"""

import csv
import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).parent


def main():
    key = {r["элемент"]: r for r in yaml.safe_load(
        (HERE / "key.yaml").read_text("utf-8"))["key"]}
    with open(HERE / "answers.csv", encoding="utf-8") as fh:
        lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
    rows = list(csv.DictReader(lines))
    if len(rows) != len(key):
        print(f"строк {len(rows)}, ожидалось {len(key)}")
        return 1

    ok = True
    for row in rows:
        want = key.get(row["элемент"])
        if want is None:
            print(f"{row['элемент']}: элемента нет в разметке")
            ok = False
            continue
        for field in ("тип", "граница", "stride"):
            got = (row.get(field) or "").strip()
            if got != want[field]:
                print(f"{row['элемент']}: {field} «{got}», "
                      f"эталон «{want[field]}» — {want['почему']}")
                ok = False
        if not (row.get("угроза") or "").strip():
            print(f"{row['элемент']}: угроза не сформулирована")
            ok = False

    print("зачтено: все шесть элементов размечены сходно с ключом"
          if ok else "не зачтено")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
