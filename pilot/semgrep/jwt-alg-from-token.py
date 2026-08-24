"""Тест-кейсы правила jwt-alg-from-token.

Разметка: строка ruleid перед ожидаемой находкой, ok перед чистым местом.
"""

import jwt


def verify_bad_no_signature(token, key):
    # ruleid: jwt-alg-from-token
    return jwt.decode(token, key, options={"verify_signature": False})


def verify_bad_verify_flag(token, key):
    # ruleid: jwt-alg-from-token
    return jwt.decode(token, key, verify=False)


def verify_bad_alg_from_header(token, key):
    header = jwt.get_unverified_header(token)
    # ruleid: jwt-alg-from-token
    return jwt.decode(token, key, algorithms=header["alg"])


def verify_bad_alg_from_header_get(token, key):
    header = jwt.get_unverified_header(token)
    # ruleid: jwt-alg-from-token
    return jwt.decode(token, key, algorithms=header.get("alg"))


def verify_bad_none_in_list(token, key):
    # ruleid: jwt-alg-from-token
    return jwt.decode(token, key, algorithms=["RS256", "none"])


def verify_good_pinned(token, key):
    # ok: jwt-alg-from-token
    return jwt.decode(token, key, algorithms=["RS256"])


def verify_good_hs(token, secret):
    # ok: jwt-alg-from-token
    return jwt.decode(token, secret, algorithms=["HS256"], audience="api")


def read_untrusted_for_message(token):
    # ok: jwt-alg-from-token
    header = jwt.get_unverified_header(token)
    return header["kid"]
