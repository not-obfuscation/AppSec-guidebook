"""Образцовое решение jwt-basics: конфиденциальные поля ушли из нагрузки.

В токене остаётся только то, что предъявителю и так известно и что нужно для
проверки: кто он, какая роль, когда выдан и когда истекает. Почта и скидочный
код лежат на сервере и достаются по проверенному `sub`, а не из нагрузки.
Подпись как проверялась, так и проверяется — целостность роли не изменилась.
"""

import time

import jwt

_SECRET = "stand-signing-secret-32-bytes-min"
_ALG = "HS256"

_USERS = {
    "wiener": {"role": "user", "email": "wiener@shop.example",
               "discount_code": "PROMO-8842-INTERNAL"},
    "administrator": {"role": "admin", "email": "admin@shop.example",
                      "discount_code": "PROMO-0001-INTERNAL"},
}


def issue(username, now=None):
    """Выдать токен сессии. В нагрузке — только несекретные поля."""
    profile = _USERS[username]
    issued = int(now if now is not None else time.time())
    return jwt.encode({
        "sub": username,
        "role": profile["role"],
        "iat": issued,
        "exp": issued + 3600,
    }, _SECRET, algorithm=_ALG)


def authorize(token, now=None):
    """Проверить подпись и срок, вернуть роль. Возвращает None при отказе."""
    try:
        claims = jwt.decode(token, _SECRET, algorithms=[_ALG])
    except jwt.InvalidTokenError:
        return None
    return claims.get("role")


def _subject(token):
    claims = jwt.decode(token, _SECRET, algorithms=[_ALG])
    return claims["sub"]


def get_discount(token):
    """Скидочный код — по проверенному sub, из серверного профиля."""
    return _USERS[_subject(token)]["discount_code"]


def get_email(token):
    """Адрес почты — по проверенному sub, из серверного профиля."""
    return _USERS[_subject(token)]["email"]
