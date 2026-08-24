"""Ключи кэша. Хеш здесь не защита, а способ укоротить строку."""
import hashlib


def key(parts):
    raw = "|".join(parts).encode()
    # ЧИСТЫЙ КОД, ПОХОЖИЙ НА ДЕФЕКТ: md5 берётся как быстрая свёртка ключа.
    return hashlib.md5(raw).hexdigest()
