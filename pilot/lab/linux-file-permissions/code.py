"""Сервис отчётов: при первом запуске пишет конфиг с токеном доступа.

Фрагмент внутреннего сервиса, сведённый к одному вопросу: с какими
правами создаётся файл, в котором лежит секрет.

Лаборатория гайдбука. Всё исполняется локально, сети не требует и
никуда не обращается. Применимо только к этой лабе.

Задача: починить создание конфига так, чтобы hack.py перестал
срабатывать, а tests.py продолжил проходить.
"""

import os


def write_config(path: str, token: str) -> None:
    """Создать конфиг с токеном или переписать его заново."""
    if not token:
        raise ValueError("пустой токен")
    # УЯЗВИМО — демонстрация, не для продакшена
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o666)
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
