"""Сервис фоновых задач: сессии пользователей и конфигурация заданий.

Упрощённый фрагмент реального сервиса. Две точки входа принимают
данные, пришедшие снаружи:

  load_session()    — восстанавливает сессию из куки браузера
  load_job_config() — читает конфигурацию задания из загруженного файла

Обе сейчас уязвимы. Задача лабораторной — починить их так, чтобы
hack.py перестал срабатывать, а tests.py продолжил проходить.
"""

import base64
import pickle
import yaml

DEFAULT_SESSION = {"user_id": None, "role": "anonymous", "cart": []}


def load_session(cookie_value: str) -> dict:
    """Восстановить сессию пользователя из значения куки.

    Куку присылает браузер, то есть значение полностью
    контролируется клиентом.
    """
    if not cookie_value:
        return dict(DEFAULT_SESSION)
    raw = base64.b64decode(cookie_value)
    return pickle.loads(raw)  # УЯЗВИМО


def dump_session(session: dict) -> str:
    """Упаковать сессию обратно в куку."""
    return base64.b64encode(pickle.dumps(session)).decode()


def load_job_config(raw_yaml: str) -> dict:
    """Прочитать конфигурацию задания из YAML.

    Файл загружает пользователь через веб-интерфейс.
    """
    return yaml.load(raw_yaml, Loader=yaml.UnsafeLoader)  # УЯЗВИМО


def run_job(config: dict) -> str:
    """Выполнить задание согласно конфигурации."""
    name = config.get("name", "unnamed")
    retries = int(config.get("retries", 0))
    return f"job={name} retries={retries}"
