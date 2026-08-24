"""Сессия без хранения состояния на самодостаточном токене.

Кабинет магазина выдаёт токен при входе и на каждом запросе читает из него
роль и внутренние поля. Токен подписан HS256, и подпись проверяется честно:
подделать роль нельзя. Дефект в другом — в полезную нагрузку положено то, что
не должно быть видно предъявителю: номер скидочного соглашения и адрес почты.
Содержимое токена читается без ключа, и «подписано» здесь не значит «скрыто».

Лаборатория гайдбука. Всё исполняется локально и применимо только к этой лабе.

Задача: убрать конфиденциальные поля из нагрузки так, чтобы hack.py перестал
их доставать, а tests.py продолжил проходить (роль, скидка и почта остаются
доступны через сервер).
"""

import time

import jwt  # PyJWT

# Секрет подписи. В настоящем приложении читается из настроек, здесь — из
# одного места модуля.
_SECRET = "stand-signing-secret-32-bytes-min"
_ALG = "HS256"

# Профиль пользователя живёт на сервере целиком.
_USERS = {
    "wiener": {"role": "user", "email": "wiener@shop.example",
               "discount_code": "PROMO-8842-INTERNAL"},
    "administrator": {"role": "admin", "email": "admin@shop.example",
                      "discount_code": "PROMO-0001-INTERNAL"},
}


# УЯЗВИМО — демонстрация, не для продакшена.
def issue(username, now=None):
    """Выдать токен сессии. Кладёт в нагрузку профиль целиком."""
    profile = _USERS[username]
    issued = int(now if now is not None else time.time())
    return jwt.encode({
        "sub": username,
        "role": profile["role"],
        "email": profile["email"],               # конфиденциально: PII
        "discount_code": profile["discount_code"],  # конфиденциально: внутреннее
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


def get_discount(token):
    """Скидочный код текущего пользователя — читается из токена."""
    claims = jwt.decode(token, _SECRET, algorithms=[_ALG])
    return claims.get("discount_code")


def get_email(token):
    """Адрес почты текущего пользователя — читается из токена."""
    claims = jwt.decode(token, _SECRET, algorithms=[_ALG])
    return claims.get("email")
