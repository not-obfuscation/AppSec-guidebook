"""Образцовое решение jwt-attacks: список алгоритмов закрыт.

Проверяющий больше не спрашивает у токена, чем его проверять. Сервер выдаёт
RS256 и принимает только RS256, сверяя подпись своим открытым ключом. alg=none
и HS256 не принимаются: подмена алгоритма отклонена до разбора нагрузки.
Роль подделать нельзя, честные токены проходят.
"""

import jwt
from cryptography.hazmat.primitives import serialization

_PRIV = None
_PUB_PEM = None
_ALLOWED = ["RS256"]


def _keys():
    global _PRIV, _PUB_PEM
    if _PRIV is None:
        reset()
    return _PRIV, _PUB_PEM


def reset():
    global _PRIV, _PUB_PEM
    from cryptography.hazmat.primitives.asymmetric import rsa
    _PRIV = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _PUB_PEM = _PRIV.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo)


def issue(username, role):
    priv, _ = _keys()
    priv_pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())
    return jwt.encode({"sub": username, "role": role}, priv_pem,
                      algorithm="RS256")


def public_key_pem():
    _, pub = _keys()
    return pub


def authorize(token):
    """Проверить подпись строго RS256 открытым ключом. None при отказе."""
    _, pub_pem = _keys()
    try:
        claims = jwt.decode(token, pub_pem.decode(), algorithms=_ALLOWED)
    except jwt.InvalidTokenError:
        return None
    return claims.get("role")
