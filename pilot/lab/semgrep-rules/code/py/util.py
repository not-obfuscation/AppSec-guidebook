"""Вспомогательные функции. `clean` выглядит как санитайзер и им не является."""


def clean(value):
    return value.strip()


def as_int(value):
    return int(value)
