"""Тест-кейсы правила jwt-confidential-claim.

Разметка: # ruleid: <id> над ожидаемой находкой, # ok: <id> над чистым местом.
"""

import time

import jwt

_SECRET = "stand-signing-secret-32-bytes-min"


def issue_bad_pii(username, profile):
    # ruleid: jwt-confidential-claim
    return jwt.encode(
        {"sub": username, "role": profile["role"],
         "email": profile["email"], "exp": int(time.time()) + 3600},
        _SECRET, algorithm="HS256")


def issue_bad_secret(username):
    # ruleid: jwt-confidential-claim
    return jwt.encode(
        {"sub": username, "api_key": "sk-live-9f2a", "exp": 1},
        _SECRET, algorithm="HS256")


def issue_bad_internal(username, code):
    # ruleid: jwt-confidential-claim
    return jwt.encode(
        {"sub": username, "discount_code": code, "role": "user"},
        _SECRET, algorithm="HS256")


def issue_good(username, role):
    # ok: jwt-confidential-claim
    return jwt.encode(
        {"sub": username, "role": role, "iat": int(time.time()),
         "exp": int(time.time()) + 3600},
        _SECRET, algorithm="HS256")


def verify(token):
    # ok: jwt-confidential-claim
    return jwt.decode(token, _SECRET, algorithms=["HS256"])
