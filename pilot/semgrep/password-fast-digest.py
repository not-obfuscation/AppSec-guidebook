"""Тест-кейсы правила password-fast-digest.

Разметка semgrep --test: строка # ruleid: <id> перед ожидаемой
находкой, # ok: <id> — перед местом, где находки быть не должно.
"""

import hashlib
import hmac
import os


def register_bad(login, password):
    # ruleid: password-fast-digest
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_bad_md5(login, password):
    # ruleid: password-fast-digest
    return hashlib.md5(password.encode()).hexdigest()


def register_bad_salted(login, password, salt):
    # ruleid: password-fast-digest
    return hashlib.sha512(salt + password.encode()).hexdigest()


def register_bad_dynamic(login, passwd):
    # ruleid: password-fast-digest
    return hashlib.new("sha256", passwd.encode()).hexdigest()


def register_good_scrypt(login, password):
    salt = os.urandom(16)
    # ok: password-fast-digest
    return hashlib.scrypt(password.encode("utf-8"), salt=salt,
                          n=2 ** 17, r=8, p=1, maxmem=192 * 1024 * 1024)


def register_good_pbkdf2(login, password):
    salt = os.urandom(16)
    # ok: password-fast-digest
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                               salt, 600_000)


def checksum_of_upload(blob):
    # ok: password-fast-digest
    return hashlib.sha256(blob).hexdigest()


def compare(stored, derived):
    # ok: password-fast-digest
    return hmac.compare_digest(stored, derived)
