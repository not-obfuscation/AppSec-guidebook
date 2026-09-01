"""Тест-кейсы правила insecure-file-mode.

Разметка semgrep --test: строка # ruleid: <id> перед ожидаемой
находкой, # ok: <id> — перед местом, где находки быть не должно.
"""

import os
import pathlib


def write_config_bad(path, text):
    # ruleid: insecure-file-mode
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o666)
    os.write(fd, text.encode("utf-8"))
    os.close(fd)


def write_public_dir_bad(path):
    # ruleid: insecure-file-mode
    fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o777)
    os.close(fd)


def loosen_bad(path):
    # ruleid: insecure-file-mode
    os.chmod(path, 0o777)


def loosen_pathlib_bad(path):
    # ruleid: insecure-file-mode
    pathlib.Path(path).chmod(0o666)


def write_config_ok(path, text):
    # ok: insecure-file-mode
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.write(fd, text.encode("utf-8"))
    os.close(fd)


def write_public_ok(path, text):
    # 0644 законно для публичного файла без секретов
    # ok: insecure-file-mode
    fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o644)
    os.write(fd, text.encode("utf-8"))
    os.close(fd)


def tighten_ok(path):
    # ok: insecure-file-mode
    os.chmod(path, 0o600)


def loosen_from_argument_ok(path, mode):
    # Слепое пятно правила: режим приходит аргументом, и какой он —
    # видно только в месте вызова, а не в этой строке.
    # ok: insecure-file-mode
    os.chmod(path, mode)
