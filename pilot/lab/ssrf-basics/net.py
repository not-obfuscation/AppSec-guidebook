"""Транспорт лабы: игрушечная сеть без единого сокета.

Ни один вызов отсюда наружу не идёт. `get()` разбирает адрес, ищет
хост в таблице имён, находит службу в таблице сети и отдаёт её ответ.
Так лаба показывает то, ради чего она заведена, — куда уходит запрос,
собранный из данных, — и при этом остаётся офлайн.

Этот файл чинить не нужно: он изображает сеть, а не приложение.
"""


class NetworkError(Exception):
    """Адрес не разобрался или по нему никто не отвечает."""


# Таблица имён: имя хоста → адрес. Разрешение имени — часть механики
# SSRF, поэтому оно вынесено отдельно и видно в коде.
DNS = {
    "partner.example": "203.0.113.10",
    "cdn.example": "203.0.113.11",
    "metadata.internal": "169.254.169.254",
    "localhost": "127.0.0.1",
}

# Файлы, видимые схеме file:. Значения — заполнители, не настоящие
# секреты.
FILES = {
    "/srv/app/.env": "DB_PASSWORD=<пароль базы>\nAPI_TOKEN=<токен>\n",
}


def _catalog(path):
    if path.startswith("/catalog/"):
        return 200, f"<товар {path.rsplit('/', 1)[-1]}, партнёр>"
    if path == "/go":
        return 302, "http://169.254.169.254/latest/meta-data/"
    return 404, ""


def _admin(path):
    if path.startswith("/admin/"):
        return 200, "session=<токен администратора>"
    return 404, ""


def _billing(path):
    if path.startswith("/invoices"):
        return 200, "счёт 7781: <сумма>, плательщик <имя>"
    return 404, ""


def _metadata(path):
    if path.startswith("/latest/meta-data/"):
        return 200, "AccessKeyId=<ключ>, Token=<временный токен>"
    return 404, ""


# Кто слушает по адресу и порту. Первая строка — единственная служба,
# к которой приложению положено обращаться.
NETWORK = {
    ("203.0.113.10", 80): _catalog,
    ("203.0.113.10", 443): _catalog,
    ("203.0.113.11", 80): _catalog,
    ("203.0.113.11", 443): _catalog,
    ("127.0.0.1", 8080): _admin,
    ("10.0.7.5", 80): _billing,
    ("169.254.169.254", 80): _metadata,
}


def split(url):
    """Разбор адреса на схему, хост, порт и путь. Без библиотек."""
    if "://" not in url:
        raise NetworkError(f"адрес без схемы: {url!r}")
    scheme, rest = url.split("://", 1)
    scheme = scheme.lower()
    if scheme == "file":
        return scheme, "", None, rest
    host, _, path = rest.partition("/")
    port = None
    if ":" in host:
        host, _, raw = host.partition(":")
        port = int(raw)
    if port is None:
        port = 443 if scheme == "https" else 80
    return scheme, host.lower(), port, "/" + path


def resolve(host):
    """Имя в адрес. Готовый адрес возвращается как есть."""
    if host in DNS:
        return DNS[host]
    if host.replace(".", "").isdigit():
        return host
    raise NetworkError(f"имя не разрешается: {host!r}")


def get(url, follow_redirects=True, hops=0):
    """Запрос по адресу. Возвращает словарь со статусом и телом."""
    scheme, host, port, path = split(url)
    if scheme == "file":
        if path in FILES:
            return {"status": 200, "body": FILES[path], "url": url}
        raise NetworkError(f"файла нет: {path!r}")
    if scheme not in ("http", "https"):
        raise NetworkError(f"схема не поддержана: {scheme!r}")
    service = NETWORK.get((resolve(host), port))
    if service is None:
        raise NetworkError(f"никто не отвечает: {host}:{port}")
    status, body = service(path)
    if status == 302 and follow_redirects:
        if hops >= 5:
            raise NetworkError("слишком много перенаправлений")
        return get(body, follow_redirects=True, hops=hops + 1)
    return {"status": status, "body": body, "url": url}
