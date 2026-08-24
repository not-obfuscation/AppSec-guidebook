"""Тест-кейсы правил aes-mode-ecb и aes-static-iv.

Разметка: # ruleid: <id> перед ожидаемой находкой, # ok: <id> — там,
где находки быть не должно.
"""

import os
import secrets

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY = os.urandom(16)
STATIC_IV = b"session-nonce-01"
STATIC_NONCE = bytes(range(16))


def encrypt_ecb(data):
    # ruleid: aes-mode-ecb
    return Cipher(algorithms.AES(KEY), modes.ECB()).encryptor().update(data)


def encrypt_ctr_static(data):
    # ruleid: aes-static-iv
    enc = Cipher(algorithms.AES(KEY), modes.CTR(STATIC_IV)).encryptor()
    return enc.update(data)


def encrypt_cbc_static(data):
    # ruleid: aes-static-iv
    enc = Cipher(algorithms.AES(KEY), modes.CBC(STATIC_NONCE)).encryptor()
    return enc.update(data)


def encrypt_ctr_fresh(data):
    iv = os.urandom(16)
    # ok: aes-static-iv
    enc = Cipher(algorithms.AES(KEY), modes.CTR(iv)).encryptor()
    return enc.update(data)


def encrypt_cbc_fresh(data):
    iv = secrets.token_bytes(16)
    # ok: aes-static-iv
    enc = Cipher(algorithms.AES(KEY), modes.CBC(iv)).encryptor()
    return enc.update(data)


def encrypt_gcm(data):
    nonce = os.urandom(12)
    # ok: aes-mode-ecb
    return AESGCM(KEY).encrypt(nonce, data, None)
