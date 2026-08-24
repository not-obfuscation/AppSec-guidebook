def get_order(conn, order_id):
    sql = f"SELECT id FROM orders WHERE id = {order_id}"
    # ruleid: sql-string-built
    return conn.execute(sql).fetchall()


def get_order_safe(conn, order_id):
    # ok: sql-string-built
    return conn.execute("SELECT id FROM orders WHERE id = ?", (order_id,))


def raw_query(conn, where):
    # ruleid: sql-string-built
    return conn.execute("SELECT id FROM orders WHERE " + where).fetchall()


def list_all(conn):
    # ok: sql-string-built
    return conn.execute("SELECT id FROM orders").fetchall()
