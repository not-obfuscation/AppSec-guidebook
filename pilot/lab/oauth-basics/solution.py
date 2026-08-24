"""Образцовое решение oauth-basics: поток кода авторизации.

Клиент просит response_type=code. Сервер авторизации переадресует с кодом в
строке запроса, а не с токеном во фрагменте. Токен доступа клиент получает по
обратному каналу обменом кода и в адрес браузера не попадает: ни в историю, ни
в Referer, ни в журналы прокси. Вход работает как прежде.
"""

from urllib.parse import urlencode, urlparse, parse_qs

_ISSUED = {}
_TOKENS = {"wiener": "AT-wiener-7a1c", "administrator": "AT-admin-0001"}

CLIENT_ID = "shop-client"
REDIRECT_URI = "https://client.shop.example/callback"


def reset():
    _ISSUED.clear()


def build_authorization_request():
    """Собрать запрос к серверу авторизации. Поток кода: токен не в ответе."""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",           # поток кода авторизации
        "scope": "openid profile",
        "state": "s-8842",
    }
    return "https://auth.shop.example/authorize?" + urlencode(params)


def authorize(request_url, username):
    query = parse_qs(urlparse(request_url).query)
    response_type = query.get("response_type", [""])[0]
    redirect = query.get("redirect_uri", [""])[0]
    state = query.get("state", [""])[0]
    token = _TOKENS[username]
    if response_type == "code":
        code = f"code-{username}-x9"
        _ISSUED[code] = token
        return f"{redirect}?code={code}&state={state}"
    if response_type == "token":
        return f"{redirect}#access_token={token}&state={state}"
    raise ValueError(f"неизвестный response_type: {response_type}")


def exchange_code(code):
    return _ISSUED.get(code)


def complete_login(redirect_url):
    parsed = urlparse(redirect_url)
    if parsed.fragment:
        fragment = parse_qs(parsed.fragment)
        return fragment.get("access_token", [None])[0]
    query = parse_qs(parsed.query)
    code = query.get("code", [None])[0]
    return exchange_code(code) if code else None
