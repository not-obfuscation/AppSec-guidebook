"""Клиент OAuth 2.0, который берёт токен доступа неявным потоком.

Модель одного приложения (client), которое входит через внешний сервер
авторизации. Сеть не поднимается: сервер авторизации — функция authorize(),
которая по запросу возвращает переадресацию обратно на client. Дефект — в типе
потока: response_type=token (неявный поток, implicit grant). Токен доступа
приходит во фрагменте адреса переадресации, то есть по фронтальному каналу
через браузер, и оседает в истории, журналах и заголовке Referer.

Лаборатория гайдбука. Всё исполняется локально и применимо только к этой лабе.

Задача: перевести клиент на поток кода авторизации (response_type=code) так,
чтобы токен доступа не появлялся в адресе переадресации, а вход продолжал
работать. hack.py должен выйти с кодом 0, tests.py — остаться зелёным.
"""

from urllib.parse import urlencode, urlparse, parse_qs

# Каталог сервера авторизации: код -> выданный токен доступа.
_ISSUED = {}
_TOKENS = {"wiener": "AT-wiener-7a1c", "administrator": "AT-admin-0001"}

CLIENT_ID = "shop-client"
REDIRECT_URI = "https://client.shop.example/callback"


def reset():
    _ISSUED.clear()


# УЯЗВИМО — демонстрация, не для продакшена.
def build_authorization_request():
    """Собрать запрос к серверу авторизации. Неявный поток: токен в ответе."""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "token",          # неявный поток (implicit grant)
        "scope": "openid profile",
        "state": "s-8842",
    }
    return "https://auth.shop.example/authorize?" + urlencode(params)


def authorize(request_url, username):
    """Сервер авторизации: аутентифицирует владельца и переадресует клиента.

    Неявный поток кладёт токен доступа во фрагмент адреса; поток кода — код в
    строке запроса.
    """
    query = parse_qs(urlparse(request_url).query)
    response_type = query.get("response_type", [""])[0]
    redirect = query.get("redirect_uri", [""])[0]
    state = query.get("state", [""])[0]
    token = _TOKENS[username]
    if response_type == "token":
        return f"{redirect}#access_token={token}&state={state}"
    if response_type == "code":
        code = f"code-{username}-x9"
        _ISSUED[code] = token
        return f"{redirect}?code={code}&state={state}"
    raise ValueError(f"неизвестный response_type: {response_type}")


def exchange_code(code):
    """Обмен кода на токен по обратному каналу. В неявном потоке не нужен."""
    return _ISSUED.get(code)


def complete_login(redirect_url):
    """Клиент разбирает ответ переадресации и достаёт токен доступа."""
    parsed = urlparse(redirect_url)
    if parsed.fragment:
        fragment = parse_qs(parsed.fragment)
        return fragment.get("access_token", [None])[0]
    query = parse_qs(parsed.query)
    code = query.get("code", [None])[0]
    return exchange_code(code) if code else None
