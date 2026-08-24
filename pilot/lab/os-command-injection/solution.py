"""Образцовое решение лабы os-command-injection.

Инструмент запускается без оболочки: аргументы передаются списком, а не
строкой. Метасимволы оболочки (`;`, `|`, `&&`) теряют силу — их некому
разбирать, подпись едет одним аргументом. Остальное — как в code.py.

Лаборатория гайдбука. Применимо только к этой лабе.
"""

import subprocess


def make_label(name):
    """Собрать подпись к отчёту и вернуть вывод инструмента."""
    result = subprocess.run(                  # (1)
        ["echo", "Отчёт:", name],             # (2)
        shell=False,
        capture_output=True, text=True)
    return result.stdout


def reset():
    return None
