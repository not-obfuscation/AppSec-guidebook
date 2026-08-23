"""Тест-кейсы правила admin-route-no-authz.

Маркер стоит строкой выше ожидаемой находки: `ruleid:` — правило
обязано сработать, `ok:` — обязано промолчать. Сверка:

    .venv-tools/bin/python pilot/semgrep/check.py admin-route
"""

app = None            # заглушки, чтобы файл читался как обычный модуль
require_role = None
current_user = None


# --- ловит -----------------------------------------------------------

# ruleid: admin-route-no-authz
@app.route("/admin/users")
def admin_users(request):
    return sorted(request["users"])


# ruleid: admin-route-no-authz
@app.route("/api/v1/admin/export", methods=("GET", "POST"))
def admin_export(request):
    return dict(request["tickets"])


# ruleid: admin-route-no-authz
@app.route("/ADMIN/reindex")
def admin_reindex(request):
    return "ok"


# --- молчит ----------------------------------------------------------

# Право объявлено у маршрута: декларативная форма.
# ok: admin-route-no-authz
@app.route("/admin/users", role="admin")
def admin_users_declared(request):
    return sorted(request["users"])


# Право проверяется в теле: императивная форма.
# ok: admin-route-no-authz
@app.route("/admin/tickets/delete", methods=("POST",))
def admin_delete(request):
    require_role("admin")
    request["tickets"].pop(request["query"]["id"], None)
    return "удалено"


# Право проверяется вторым декоратором.
# ok: admin-route-no-authz
@app.route("/admin/settings")
@require_role("admin")
def admin_settings(request):
    return request["settings"]


# Маршрут не административный: правило про него ничего не знает.
# ok: admin-route-no-authz
@app.route("/profile")
def profile(request):
    return {"login": current_user}
