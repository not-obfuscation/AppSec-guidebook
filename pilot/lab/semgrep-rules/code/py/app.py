"""Точки входа. Параметры запроса приходят сюда и расходятся по модулям."""
from urllib.parse import parse_qs

from . import cache, db, report, util


def handle_order(conn, query_string):
    params = parse_qs(query_string)
    order_id = params.get("id", [""])[0]
    return db.get_order(conn, order_id)


def handle_search(conn, query_string):
    params = parse_qs(query_string)
    where = util.clean(params.get("where", [""])[0])
    return db.raw_query(conn, where)


def handle_export(query_string):
    params = parse_qs(query_string)
    fmt = params.get("fmt", ["csv"])[0]
    return report.export(fmt, "/etc/hostname")


def handle_page(query_string):
    params = parse_qs(query_string)
    return cache.key(["page", params.get("n", ["1"])[0]])
