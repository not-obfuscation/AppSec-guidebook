"""Песочница лабы: дерево каталогов, одинаковое для code.py и solution.py.

Создаётся один раз на процесс во временном каталоге. Секрет лежит РЯДОМ с
базовым каталогом, а не внутри: в этом и смысл — выход за базовый каталог
должен быть невозможен.

    <root>/
      documents/            <- базовый каталог выдачи
        invoice-2026-01.txt
        invoice-2026-02.txt
        archive/
          invoice-2025-12.txt
        notes.txt           -> символическая ссылка на ../service.env
      service.env           <- вне базового каталога, выдаче не подлежит
"""

import os
import pathlib
import tempfile

SECRET_LINE = "SERVICE_API_TOKEN=lab-only-not-a-real-secret"

_root = None


def root():
    """Каталог песочницы. Создаётся при первом обращении."""
    global _root
    if _root is not None:
        return _root
    _root = pathlib.Path(tempfile.mkdtemp(prefix="lab-path-traversal-"))
    base = _root / "documents"
    (base / "archive").mkdir(parents=True)
    (base / "invoice-2026-01.txt").write_text(
        "счёт за январь: 1200\n", encoding="utf-8")
    (base / "invoice-2026-02.txt").write_text(
        "счёт за февраль: 1450\n", encoding="utf-8")
    (base / "archive" / "invoice-2025-12.txt").write_text(
        "счёт за декабрь: 990\n", encoding="utf-8")
    (_root / "service.env").write_text(SECRET_LINE + "\n", encoding="utf-8")
    os.symlink(_root / "service.env", base / "notes.txt")
    return _root


def base():
    """Базовый каталог выдачи документов."""
    return root() / "documents"


def secret_path():
    """Файл, который выдаче не подлежит."""
    return root() / "service.env"
