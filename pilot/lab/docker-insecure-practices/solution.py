"""Модель: контейнер мониторинга — эталонная починка.

Отличие от code.py одно: контейнер получает не сокет демона целиком,
а узкий канал, который умеет ровно одно — отдать список контейнеров.
Это образ прокси перед сокетом: чтение разрешено, создание контейнеров
через канал невозможно.

Это модель: настоящий Docker не нужен, привилегии не повышаются.

Лаборатория гайдбука. Применимо только к этой лабе.
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
    """Контейнер мониторинга: его задача — список контейнеров хоста."""

    def channel(method: str, path: str, spec: dict | None = None):
        """Узкий канал вместо сокета: только чтение списка."""
        if (method, path) != ("GET", "/containers/json"):
            return 403, None
        return daemon.handle(method, path, spec)

    def report() -> str:
        code, names = channel("GET", "/containers/json")
        if code != 200:
            raise RuntimeError(f"демон ответил {code}")
        return f"контейнеров на хосте: {len(names)}"

    return channel, report
