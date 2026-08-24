"""Образцовое решение: адрес собирает приложение, а не клиент.

Отличий от `code.py` три, и все три обязательны по отдельности:
разрешённая схема, разрешённый адрес назначения после разрешения
имени, запрет ходить по перенаправлениям.
"""

import net

PARTNERS = ("partner.example", "cdn.example")

# Схемы, которые витрине нужны. Всё прочее — file:, gopher:, dict: —
# в исходящем запросе не нужно никогда.
SCHEMES = ("http", "https")


class Denied(Exception):
    """Отказ собрать исходящий запрос. Обработчик даёт 400."""


def allowed_url(url):
    """Адрес из списка разрешённого либо отказ. Другого выхода нет."""
    try:
        scheme, host, port, path = net.split(url)
    except net.NetworkError as exc:
        raise Denied(f"адрес не разбирается: {exc}") from exc
    if scheme not in SCHEMES:
        raise Denied(f"схема не разрешена: {scheme}")
    if host not in PARTNERS:
        raise Denied(f"хост не в списке партнёров: {host}")
    try:
        address = net.resolve(host)
    except net.NetworkError as exc:
        raise Denied(f"имя не разрешается: {exc}") from exc
    if (address, port) not in ALLOWED_ADDRESSES:
        raise Denied(f"адрес назначения не разрешён: {address}:{port}")
    return f"{scheme}://{host}:{port}{path}"


# Куда партнёрским именам позволено разрешаться. Проверка адреса, а не
# имени, закрывает случай «имя в списке, адрес внутренний».
ALLOWED_ADDRESSES = frozenset({
    ("203.0.113.10", 80), ("203.0.113.11", 80),
    ("203.0.113.10", 443), ("203.0.113.11", 443),
})


def preview(request):
    """Показать карточку товара по адресу, который прислал клиент."""
    url = request["query"].get("url", "")
    if not url:
        raise Denied("адрес не указан")
    target = allowed_url(url)
    resp = net.get(target, follow_redirects=False)
    if resp["status"] == 302:
        raise Denied("перенаправление не проходится")
    return {"status": 200, "body": resp["body"], "fetched": resp["url"]}


def handle(url):
    """Единая точка входа лабы: собрать запрос и отдать обработчику."""
    try:
        return preview({"query": {"url": url}})
    except Denied as exc:
        return {"status": 400, "body": str(exc), "fetched": None}
    except net.NetworkError as exc:
        return {"status": 502, "body": str(exc), "fetched": None}
