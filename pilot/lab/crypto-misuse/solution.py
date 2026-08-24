"""Образец починки: один аутентифицированный режим и проверка до разбора.

AES-GCM шифрует и заверяет состояние одним вызовом, а одноразовое значение
берётся свежим на каждую выдачу и хранится рядом с шифротекстом. Присланное
значение проверяется меткой прежде, чем из него что-то достают: подделка
отвергается, а не разбирается.

Демонстрация для лабы, не для продакшена.
"""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

import sandbox


def issue_profile(user: str, role: str, credit: int) -> str:
    return _seal(sandbox.make_state(user, role, credit))


def load_profile(cookie: str) -> dict:
    return sandbox.parse_state(_open(cookie))


def issue_session(user: str, role: str, credit: int) -> str:
    return _seal(sandbox.make_state(user, role, credit))


def load_session(cookie: str) -> dict:
    return sandbox.parse_state(_open(cookie))


def _seal(state: str) -> str:
    nonce = os.urandom(12)                       # свежее на каждую выдачу
    g = AESGCM(sandbox.APP_KEY)
    ct = g.encrypt(nonce, state.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def _open(cookie: str) -> str:
    raw = base64.b64decode(cookie)
    nonce, ct = raw[:12], raw[12:]
    g = AESGCM(sandbox.APP_KEY)
    plain = g.decrypt(nonce, ct, None)           # InvalidTag до всякого разбора
    return plain.decode("utf-8", "replace")


class Rejected(Exception):
    """Проверка целостности не прошла — значение подделано."""


def safe_open(cookie: str) -> dict:
    try:
        return sandbox.parse_state(_open(cookie))
    except InvalidTag:
        raise Rejected("подделанное значение отвергнуто")
