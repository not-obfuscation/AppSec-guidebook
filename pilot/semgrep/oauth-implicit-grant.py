"""Тест-кейсы правила oauth-implicit-grant.

Разметка: строка ruleid над ожидаемой находкой, ok над чистым местом.
"""


def build_bad_implicit(client_id, redirect):
    # ruleid: oauth-implicit-grant
    return {
        "client_id": client_id,
        "redirect_uri": redirect,
        "response_type": "token",
        "state": "s",
    }


def build_bad_password(username, password):
    # ruleid: oauth-implicit-grant
    return {
        "grant_type": "password",
        "username": username,
        "password": password,
    }


def set_bad_implicit(params):
    # ruleid: oauth-implicit-grant
    params["response_type"] = "token"
    return params


def build_good_code(client_id, redirect):
    # ok: oauth-implicit-grant
    return {
        "client_id": client_id,
        "redirect_uri": redirect,
        "response_type": "code",
        "state": "s",
    }


def build_good_refresh(refresh_token):
    # ok: oauth-implicit-grant
    return {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
