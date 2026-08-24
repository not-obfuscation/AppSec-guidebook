"""Выгрузка отчёта во внешний конвертер."""
import subprocess

FORMATS = {"csv", "tsv"}


def export(fmt, path):
    # ПОДСТАВЛЕННЫЙ ДЕФЕКТ 3: shell=True и подстановка параметра запроса.
    cmd = f"/usr/bin/env cat {path} | /usr/bin/env tr ',' '{fmt}'"
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def export_safe(fmt, path):
    if fmt not in FORMATS:
        raise ValueError("unknown format")
    sep = "," if fmt == "csv" else "\t"
    return subprocess.run(
        ["/usr/bin/env", "tr", ",", sep], stdin=open(path), capture_output=True
    )
