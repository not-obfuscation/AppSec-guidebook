"""Модель: контейнер мониторинга с примонтированным сокетом демона.

Мониторингу на хосте нужно видеть список контейнеров. Чтобы «не возиться
с правами», контейнеру примонтировали сокет демона целиком —
/var/run/docker.sock. Тот, кто исполнит свой код внутри этого
контейнера, говорит с демоном наравне с root хоста.

Это модель: демон, его API и контейнер изображены структурами данных
Python. Настоящий Docker не нужен, привилегии не повышаются.

Лаборатория гайдбука. Всё исполняется локально, сети не требует и
никуда не обращается. Применимо только к этой лабе.

Задача: починить контейнер мониторинга так, чтобы hack.py перестал
срабатывать, а tests.py продолжил проходить.
"""


class Daemon:
    """Демон контейнеров: хранит список и исполняет запросы API."""

    def __init__(self) -> None:
        self.containers: list = []

    def handle(self, method: str, path: str, spec: dict | None = None):
        """Единая точка входа API демона."""
        if method == "GET" and path == "/containers/json":
            return 200, [c["name"] for c in self.containers]
        if method == "POST" and path == "/containers/create":
            self.containers.append(spec)
            return 201, spec["name"]
        return 404, None


def monitoring_container(daemon: Daemon):
    """Контейнер мониторинга: его задача — список контейнеров хоста.

    Возвращает пару (канал, report): канал — то, что контейнер получил
    от хоста, report — рабочая функция мониторинга.
    """
    # УЯЗВИМО — демонстрация, не для продакшена: канал к демону — это
    # полный сокет, контейнер может вызвать любую точку API.
    channel = daemon.handle

    def report() -> str:
        code, names = channel("GET", "/containers/json")
        if code != 200:
            raise RuntimeError(f"демон ответил {code}")
        return f"контейнеров на хосте: {len(names)}"

    return channel, report
