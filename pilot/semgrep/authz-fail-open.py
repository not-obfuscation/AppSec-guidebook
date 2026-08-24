"""Тест-кейсы правил authz-broad-except-allow и
authz-default-allow-on-missing-decision.

Разметка: # ruleid: <id> перед ожидаемой находкой, # ok: <id> — там,
где находки быть не должно.
"""


class PolicyUnavailable(Exception):
    pass


def check(user, action):
    return {"allow": user == "root"}


def authorize_broad(user, action):
    # ruleid: authz-broad-except-allow
    try:
        return check(user, action)["allow"]
    except Exception:
        return True


def authorize_bare(user, action):
    # ruleid: authz-broad-except-allow
    try:
        return check(user, action)["allow"]
    except:
        return True


def authorize_specific(user, action):
    # ok: authz-broad-except-allow
    try:
        return check(user, action)["allow"]
    except PolicyUnavailable:
        return False


def authorize_broad_denies(user, action):
    # ok: authz-broad-except-allow
    try:
        return check(user, action)["allow"]
    except Exception:
        return False


def read_answer_default_allow(answer):
    # ruleid: authz-default-allow-on-missing-decision
    return answer.get("allow", True)


def read_answer_default_granted(answer):
    # ruleid: authz-default-allow-on-missing-decision
    return answer.get("granted", True)


def read_answer_default_deny(answer):
    # ok: authz-default-allow-on-missing-decision
    return answer.get("allow", False)


def read_answer_explicit(answer):
    # ok: authz-default-allow-on-missing-decision
    if "allow" not in answer:
        raise PolicyUnavailable("no decision")
    return answer["allow"]


def unrelated_default_true(config):
    # ok: authz-default-allow-on-missing-decision
    return config.get("retry", True)
