"""Тест-кейсы правила outbound-url-unvalidated.

Маркер стоит строкой выше ожидаемой находки: `ruleid:` — правило
обязано сработать, `ok:` — обязано промолчать. Маркер таинт-правила
адресуется строке стока, то есть строке с вызовом клиента. Сверка:

    .venv-tools/bin/python pilot/semgrep/check.py outbound-url
"""

import net
import requests
from urllib.request import urlopen

PARTNERS = ("partner.example",)
CATALOG = "https://partner.example/catalog"


def allowed_url(url):
    """Сверка и пересборка адреса из разрешённых частей."""
    host = url.split("://", 1)[-1].split("/")[0]
    if host not in PARTNERS:
        raise ValueError("хост не разрешён")
    return f"https://{host}/catalog"


# --- ловит -----------------------------------------------------------

def preview(request):
    url = request["query"].get("url", "")
    # ruleid: outbound-url-unvalidated
    return net.get(url)


def avatar(request):
    # ruleid: outbound-url-unvalidated
    return requests.get(request["avatar_url"], timeout=5)


def webhook(request):
    target = request["json"]["callback"]
    # ruleid: outbound-url-unvalidated
    return requests.post(url=target, json={"ok": True})


def importer(request):
    # ruleid: outbound-url-unvalidated
    return urlopen(request["query"]["source"]).read()


# --- молчит ----------------------------------------------------------

def preview_checked(request):
    """Адрес прошёл сверку со списком разрешённого."""
    target = allowed_url(request["query"].get("url", ""))
    # ok: outbound-url-unvalidated
    return net.get(target)


def preview_by_id(request):
    """Адрес задан приложением, из запроса приходит только номер."""
    item = int(request["query"]["id"])
    # ok: outbound-url-unvalidated
    return requests.get(f"{CATALOG}/{item}", timeout=5)


def health():
    """Клиент вызывается без адреса из запроса вовсе."""
    # ok: outbound-url-unvalidated
    return requests.get(CATALOG, timeout=5)
