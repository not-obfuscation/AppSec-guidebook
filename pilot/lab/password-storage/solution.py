"""Образцовое решение лабы: то же хранилище, но пароль хранится иначе.

Разбор — в теме `password-storage`, блок 6. Здесь только код.
"""

import base64
import hashlib
import hmac
import os

_STORE: dict[str, str] = {}

# Параметры scrypt из Password Storage Cheat Sheet для p=1.
_N = 2 ** 17
_R = 8
_P = 1
# OpenSSL отказывается считать, если запрошенная память больше maxmem,
# а его умолчание — 32 МиБ. Этим параметрам нужно 128 * N * r и ещё
# 128 * r * p + 256 * r байт сверху, то есть чуть больше 128 МиБ.
# Без явного предела вызов падает с ValueError.
_MAXMEM = 192 * 1024 * 1024
_SALT_BYTES = 16
_DKLEN = 32


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt,
                          n=_N, r=_R, p=_P, maxmem=_MAXMEM, dklen=_DKLEN)


def _encode(salt: bytes, derived: bytes) -> str:
    params = f"n={_N},r={_R},p={_P}"
    return f"scrypt${params}${_b64(salt)}${_b64(derived)}"


def register(login: str, password: str) -> None:
    """Завести учётную запись."""
    salt = os.urandom(_SALT_BYTES)
    _STORE[login] = _encode(salt, _derive(password, salt))


def _verify_scrypt(password: str, stored: str) -> bool:
    _, params, salt_b64, hash_b64 = stored.split("$")
    values = dict(pair.split("=") for pair in params.split(","))
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=base64.b64decode(salt_b64),
        n=int(values["n"]), r=int(values["r"]), p=int(values["p"]),
        maxmem=_MAXMEM,
        dklen=len(base64.b64decode(hash_b64)))
    return hmac.compare_digest(derived, base64.b64decode(hash_b64))


def _verify_legacy(password: str, stored: str) -> bool:
    # Здесь пароль не сохраняется, а сверяется с записью старого
    # формата; правило password-fast-digest этих двух случаев не
    # различает, разбор — в теме, блок 8.
    # nosemgrep: password-fast-digest
    candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(candidate, stored)


def verify(login: str, password: str) -> bool:
    """Проверить пару логин-пароль.

    Записи старого формата принимаются и при удачном входе
    переписываются на новый: исходного пароля больше нигде нет, и
    другого момента, когда он окажется в руках, не будет.
    """
    stored = _STORE.get(login)
    if stored is None:
        return False
    if stored.startswith("scrypt$"):
        return _verify_scrypt(password, stored)
    if not _verify_legacy(password, stored):
        return False
    register(login, password)
    return True


def load_legacy(login: str, sha256_hex: str) -> None:
    """Внести запись из старой базы: голый SHA-256 без соли."""
    _STORE[login] = sha256_hex


def export_dump() -> list[tuple[str, str]]:
    """Содержимое таблицы — то же, что уйдёт с резервной копией."""
    return sorted(_STORE.items())


def reset() -> None:
    """Очистить хранилище."""
    _STORE.clear()
