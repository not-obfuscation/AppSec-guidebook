"""Проверка токена, которая берёт алгоритм из самого токена.

Кабинет отдаёт роль по JWT. Проверяющий читает поле alg из заголовка и по нему
решает, чем сверять подпись: none — не сверять вовсе, HS256 — общим секретом,
RS256 — открытым ключом. Заголовок приходит от предъявителя и до проверки
подписи ничем не защищён, поэтому предъявитель управляет тем, как его же токен
будут проверять. Отсюда два обхода: alg=none и подмена RS256 на HS256.

Лаборатория гайдбука. Всё исполняется локально и применимо только к этой лабе.

Задача: закрыть список принимаемых алгоритмов и разорвать связь «алгоритм из
заголовка → способ проверки», чтобы hack.py перестал срабатывать, а tests.py
продолжил проходить.
"""

import base64
import hashlib
import hmac
import json

import jwt  # PyJWT

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

# Сервер подписывает RS256 своим закрытым ключом и раздаёт открытый.
_PRIV = None
_PUB_PEM = None


def _keys():
    global _PRIV, _PUB_PEM
    if _PRIV is None:
        reset()
    return _PRIV, _PUB_PEM


def reset():
    """Свежая пара ключей RS256. Открытый ключ не секрет."""
    global _PRIV, _PUB_PEM
    from cryptography.hazmat.primitives.asymmetric import rsa
    _PRIV = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _PUB_PEM = _PRIV.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo)


def _b64u(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _unb64u(part):
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def issue(username, role):
    """Выдать честный токен RS256."""
    priv, _ = _keys()
    header = _b64u(json.dumps({"alg": "RS256", "typ": "JWT"},
                              separators=(",", ":")).encode())
    payload = _b64u(json.dumps({"sub": username, "role": role},
                               separators=(",", ":")).encode())
    signature = priv.sign(f"{header}.{payload}".encode(),
                          padding.PKCS1v15(), hashes.SHA256())
    return f"{header}.{payload}.{_b64u(signature)}"


def public_key_pem():
    """Открытый ключ сервера — его сервер и так публикует."""
    _, pub = _keys()
    return pub


# УЯЗВИМО — демонстрация, не для продакшена.
def authorize(token):
    """Вернуть роль, проверив подпись алгоритмом ИЗ ЗАГОЛОВКА токена."""
    _, pub_pem = _keys()
    try:
        h_raw, p_raw, sig = token.split(".")
        alg = json.loads(_unb64u(h_raw)).get("alg")
    except (ValueError, json.JSONDecodeError):
        return None
    signing_input = f"{h_raw}.{p_raw}".encode()

    if alg == "none":
        # «раз токен говорит none — проверять нечего»
        claims = jwt.decode(token, options={"verify_signature": False})
    elif alg == "HS256":
        want = _b64u(hmac.new(pub_pem, signing_input,       # ключ — открытый PEM
                              hashlib.sha256).digest())
        if not hmac.compare_digest(want, sig):
            return None
        claims = json.loads(_unb64u(p_raw))
    elif alg == "RS256":
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        try:
            load_pem_public_key(pub_pem).verify(
                _unb64u(sig), signing_input, padding.PKCS1v15(), hashes.SHA256())
        except Exception:
            return None
        claims = json.loads(_unb64u(p_raw))
    else:
        return None
    return claims.get("role")
