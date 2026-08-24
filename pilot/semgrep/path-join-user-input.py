"""Тест-кейсы правила path-join-user-input.

Разметка: строка ruleid над ожидаемой находкой, строка ok над чистым местом.
"""

import os
import os.path

BASE = "/var/www/documents"


def read_no_check(name):
    """Ни проверки, ни канонизации."""
    path = os.path.join(BASE, name)
    # ruleid: path-join-user-input
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_prefix_before_canon(name):
    """Префикс сверяется на неканонизированном пути — сверка бесполезна."""
    path = os.path.join(BASE, name)
    if not path.startswith(BASE):
        raise PermissionError("вне базового каталога")
    # ruleid: path-join-user-input
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_canonical(name):
    """Канонизация до сверки: realpath, затем commonpath."""
    base = os.path.realpath(BASE)
    path = os.path.realpath(os.path.join(base, name))
    if os.path.commonpath([base, path]) != base:
        raise PermissionError("вне базового каталога")
    # ok: path-join-user-input
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_fixed_name():
    """Имя не приходит извне, join собирает постоянный путь."""
    path = os.path.join(BASE, "index.txt")
    # ruleid: path-join-user-input
    with open(path, encoding="utf-8") as f:
        return f.read()
