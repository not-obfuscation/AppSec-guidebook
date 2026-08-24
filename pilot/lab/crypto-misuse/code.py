"""УЯЗВИМЫЙ образец: состояние сессии на клиенте под AES без целостности.

Два вида cookie. Профиль шифруется режимом ECB, сеанс — режимом счётчика с
постоянным одноразовым значением. Метки целостности нет ни у того, ни у
другого, а расшифровке присланного ничего не предшествует.

Демонстрация для лабы, не для продакшена.
"""

import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import sandbox

FIXED_NONCE = b"session-nonce-01"          # одно значение на всё приложение


def _pad(data: bytes) -> bytes:
    n = sandbox.BLOCK - len(data) % sandbox.BLOCK
    return data + bytes([n]) * n


def _unpad(data: bytes) -> bytes:
    return data[:-data[-1]]


def issue_profile(user: str, role: str, credit: int) -> str:
    """Профиль в cookie: AES в режиме ECB."""
    plain = _pad(sandbox.make_state(user, role, credit).encode())
    enc = Cipher(algorithms.AES(sandbox.APP_KEY), modes.ECB()).encryptor()
    return base64.b64encode(enc.update(plain) + enc.finalize()).decode()


def load_profile(cookie: str) -> dict:
    raw = base64.b64decode(cookie)
    dec = Cipher(algorithms.AES(sandbox.APP_KEY), modes.ECB()).decryptor()
    plain = _unpad(dec.update(raw) + dec.finalize())
    return sandbox.parse_state(plain.decode("utf-8", "replace"))


def issue_session(user: str, role: str, credit: int) -> str:
    """Сеанс в cookie: режим счётчика с постоянным одноразовым значением."""
    plain = sandbox.make_state(user, role, credit).encode()
    enc = Cipher(algorithms.AES(sandbox.APP_KEY),
                 modes.CTR(FIXED_NONCE)).encryptor()
    return base64.b64encode(enc.update(plain) + enc.finalize()).decode()


def load_session(cookie: str) -> dict:
    raw = base64.b64decode(cookie)
    dec = Cipher(algorithms.AES(sandbox.APP_KEY),
                 modes.CTR(FIXED_NONCE)).decryptor()
    return sandbox.parse_state(dec.update(raw).decode("utf-8", "replace"))
