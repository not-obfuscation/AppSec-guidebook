"""Образец починки: канонизация пути до сверки с базовым каталогом.

Порядок операций перевёрнут против code.py. Сначала путь приводится к
каноническому виду — `os.path.realpath` убирает `.` и `..` и разворачивает
символические ссылки, — и только потом проверяется принадлежность базовому
каталогу. Сравнение идёт через `os.path.commonpath`, а не `startswith`: иначе
каталог-сосед с общим началом имени (`documents-old`) прошёл бы проверку.

Функциональность не меняется: подкаталоги и `..` внутри базового каталога
работают, потому что канонический путь остаётся внутри.
"""

import os
import os.path

import sandbox


def list_documents():
    """Имена документов, доступных клиенту."""
    base = str(sandbox.base())
    return sorted(
        name for name in os.listdir(base)
        if os.path.isfile(os.path.join(base, name))
    )


def read_document(name):
    """Отдать документ по имени. Имя приходит от клиента."""
    base = os.path.realpath(str(sandbox.base()))
    path = os.path.realpath(os.path.join(base, name))   # сначала канонизация
    if os.path.commonpath([base, path]) != base:        # потом сверка
        raise PermissionError("вне базового каталога")
    with open(path, encoding="utf-8") as f:
        return f.read()
