"""Сервис отчётов: эталонная починка хранения конфига с токеном.

Отличие от code.py одно: режим файла запрошен явно и не шире 0600,
поэтому ни umask процесса, ни настройки окружения не сделают конфиг
читаемым для группы или остальных.

Лаборатория гайдбука. Всё исполняется локально, сети не требует и
никуда не обращается. Применимо только к этой лабе.
"""

import os


def write_config(path: str, token: str) -> None:
    """Создать конфиг с токеном или переписать его заново."""
    if not token:
        raise ValueError("пустой токен")
    # Режим задан явно: umask может только срезать биты, шире 0600
    # файл при таком вызове не станет ни при какой маске.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, f"token={token}\n".encode("utf-8"))
    finally:
        os.close(fd)


def read_config(path: str) -> str:
    """Прочитать токен из конфига."""
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("token="):
                return line[len("token="):].strip()
    raise ValueError("в конфиге нет token=")


def ensure_config(path: str, token: str) -> None:
    """Завести конфиг, только если его ещё нет."""
    if not os.path.exists(path):
        write_config(path, token)
