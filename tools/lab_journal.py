#!/usr/bin/env python3
"""Прогон лаб по рабочей копии читателя — сводка для журнала вне сайта.

    .venv-tools/bin/python tools/lab_journal.py                  # все 37 лаб
    .venv-tools/bin/python tools/lab_journal.py idor vault       # выборочно

Зачем отдельный скрипт рядом с `run_labs.py`. `make labs` доказывает, что лаба
решаема: эталон из `solution/` применяется во временной копии, рабочие файлы не
трогаются. Журналу читателя (research/10 § 5.3, решение оператора 2026-10-01,
п. 7) нужно обратное — состояние его собственных файлов: `code.py` как он его
оставил, его `answers.csv`, его правила в `rules/`. Поэтому здесь всё гоняется
по рабочей копии на месте, без подмены эталоном.

Критерии и способы запуска — те, что заведены самими лабами (свой контур не
выдумывается):

  «почини» (20 Python-лаб)   `tests.py` зелёные и `hack.py` отвечает 0
                             (эксплойт не проходит) при `LAB_TARGET=code.py`;
  браузерные (5 лаб)         то же для `tests.mjs`/`hack.mjs` под node с тем же
                             chrome-headless-shell, что рисует схемы;
  `semgrep-rules`            `./check.sh` — прогон разметки на правилах читателя;
  задачи чтения и починки    `check.py` лабы на её рабочих файлах: cve-cvss,
  со своей проверялкой       sast-principles, threat-modeling, owasp-asvs,
                             supply-chain-threats, pipeline-anatomy,
                             pipeline-security, quality-gates;
  стендовые                  zap-scanning (check.py + `check_fix.py` на стенде),
                             developer-communication и vault — стенд поднимается
                             перед проверкой и гасится за собой, порты после
                             прогона проверяются, как в `run_labs.py`.

Статусы: «закрыта» — проверки лабы сошлись на рабочей копии; «не закрыта» —
штатное состояние непройденной лабы; «не проверена» — нет инструмента (node,
chrome-headless-shell, vault, docker) или прогон не ответил. Последнее — не
оценка читателя, а состояние обвязки, поэтому и считается отдельно.

Выход всегда 0: это учётный прогон, а не гейт. Код 2 — неизвестные имена лаб.
"""

import datetime as dt
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import LABS_YAML, ROOT
from run_labs import FIX_PY, FIX_JS, LABS, PORTS, PY, SEMGREP

CLOSED, OPEN, SKIPPED = "закрыта", "не закрыта", "не проверена"

# Четыре стендовых и полустендовых вида поимённо; остальные нестандартные лабы
# проверяются своей `check.py` на рабочих файлах, без поднятия чего-либо.
CHECK_PY = ["cve-cvss", "sast-principles", "threat-modeling", "owasp-asvs",
            "supply-chain-threats", "pipeline-anatomy", "pipeline-security",
            "quality-gates"]


def run(argv: list, cwd: Path, env: dict | None = None,
        timeout: int = 300) -> subprocess.CompletedProcess | None:
    """Один прогон; None — таймаут (проверка не ответила, вердикта нет)."""
    try:
        return subprocess.run([str(a) for a in argv], cwd=cwd, env=env,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    except OSError:
        return None


def tail(proc: subprocess.CompletedProcess | None, n: int = 3) -> str:
    """Хвост вывода для детали статуса: читатель чинит по нему, не перезапуская."""
    if proc is None:
        return "таймаут — проверь, не зависает ли код"
    lines = (proc.stdout + proc.stderr).strip().splitlines()
    return "; ".join(line.strip() for line in lines[-n:] if line.strip())[:200]


def stand(lab: Path, cmd: str, env: dict | None = None,
          timeout: int = 120) -> subprocess.CompletedProcess | None:
    return run(["sh", "stand.sh", cmd], lab, env=env, timeout=timeout)


# --- виды лаб ---------------------------------------------------------------

def fix_py(name: str) -> tuple[str, str]:
    lab = LABS / name
    env = os.environ | {"LAB_TARGET": "code.py"}
    tests = run([PY, "tests.py"], lab, env=env)
    if tests is None or tests.returncode != 0:
        return OPEN, f"функциональные тесты падают: {tail(tests)}"
    hack = run([PY, "hack.py"], lab, env=env)
    if hack is None or hack.returncode not in (0, 1):
        return SKIPPED, f"hack.py не ответил кодом 0/1: {tail(hack)}"
    if hack.returncode == 1:
        return OPEN, "эксплойт проходит — дефект на месте"
    return CLOSED, "тесты зелёные, эксплойт не проходит"


def fix_js(name: str, ext: str) -> tuple[str, str]:
    lab = LABS / name
    env = os.environ | {"LAB_TARGET": f"code.{ext}"}
    tests = run(["node", "tests.mjs"], lab, env=env, timeout=600)
    if tests is None or tests.returncode != 0:
        return OPEN, f"функциональные тесты падают: {tail(tests)}"
    hack = run(["node", "hack.mjs"], lab, env=env, timeout=600)
    if hack is None or hack.returncode not in (0, 1):
        return SKIPPED, f"hack.mjs не ответил кодом 0/1: {tail(hack)}"
    if hack.returncode == 1:
        return OPEN, "эксплойт проходит — дефект на месте"
    return CLOSED, "тесты зелёные, эксплойт не проходит"


def check_py(name: str) -> tuple[str, str]:
    proc = run([PY, "check.py"], LABS / name)
    if proc is None:
        return SKIPPED, tail(proc)
    if proc.returncode == 0:
        return CLOSED, "check.py сошлась на рабочих файлах"
    if proc.returncode == 1:
        return OPEN, f"check.py не зачла: {tail(proc)}"
    return SKIPPED, f"check.py упала: {tail(proc)}"


def semgrep_rules() -> tuple[str, str]:
    if not SEMGREP.exists():
        return SKIPPED, "нет semgrep — `make setup`"
    proc = run(["sh", "check.sh"], LABS / "semgrep-rules", timeout=600)
    if proc is None:
        return SKIPPED, tail(proc)
    if proc.returncode == 0:
        return CLOSED, "разметка ожиданий сошлась на правилах из rules/"
    return OPEN, f"разметка не сходится: {tail(proc)}"


def zap_scanning() -> tuple[str, str]:
    lab = LABS / "zap-scanning"
    status, detail = check_py("zap-scanning")
    if status != CLOSED:
        return status, "разбор отчёта: " + detail
    # Задача «почини»: стенд сбрасывается (журнал и заметки, не app.py —
    # правка читателя в stand/app.py сбросом не трогается) и гасится за собой.
    try:
        if stand(lab, "reset") is None:
            return SKIPPED, "стенд не поднялся: таймаут"
        proc = run([PY, "check_fix.py"], lab)
        if proc is None:
            return SKIPPED, tail(proc)
        if proc.returncode == 0:
            return CLOSED, "отчёт разобран, починка зачтена"
        if proc.returncode == 1:
            return OPEN, f"отчёт зачтён, починка нет: {tail(proc)}"
        return SKIPPED, f"check_fix.py упала: {tail(proc)}"
    finally:
        stand(lab, "stop")


def developer_communication() -> tuple[str, str]:
    lab = LABS / "developer-communication"
    try:
        started = stand(lab, "start")
        if started is None or started.returncode != 0:
            return SKIPPED, f"стенд не поднялся: {tail(started)}"
        proc = run([PY, "check.py"], lab)
        if proc is None:
            return SKIPPED, tail(proc)
        if proc.returncode == 0:
            return CLOSED, "все три заявки воспроизводятся на стенде"
        if proc.returncode == 1:
            return OPEN, f"заявки не зачтены: {tail(proc)}"
        return SKIPPED, f"check.py упала: {tail(proc)}"
    finally:
        stand(lab, "stop")


def vault() -> tuple[str, str]:
    # Порядок поиска бинарника тот же, что в run_labs.py: VAULT_BIN → PATH →
    # tools/bin/vault; docker нужен стенду под postgres.
    env = os.environ.copy()
    if "VAULT_BIN" not in env and not shutil.which("vault"):
        candidate = ROOT / "tools" / "bin" / "vault"
        if candidate.exists():
            env["VAULT_BIN"] = str(candidate)
        else:
            return SKIPPED, "нет бинарника vault (VAULT_BIN, PATH, tools/bin)"
    if not shutil.which("docker"):
        return SKIPPED, "нет docker: стенд поднимает postgres в контейнере"
    lab = LABS / "vault"
    try:
        started = stand(lab, "start", env=env, timeout=180)
        if started is None or started.returncode != 0:
            return SKIPPED, f"стенд не поднялся: {tail(started)}"
        stand(lab, "reset", env=env)
        proc = run([PY, "check.py"], lab, env=env)
        if proc is None:
            return SKIPPED, tail(proc)
        if proc.returncode == 0:
            return CLOSED, "выдача по политике из рабочих .hcl/.sql зачтена"
        if proc.returncode == 1:
            return OPEN, f"выдача не зачтена: {tail(proc)}"
        return SKIPPED, f"check.py упала: {tail(proc)}"
    finally:
        stand(lab, "stop", env=env)


SPECIAL = {
    "semgrep-rules": semgrep_rules,
    "zap-scanning": zap_scanning,
    "developer-communication": developer_communication,
    "vault": vault,
}


def chrome_available() -> bool:
    """Та же проверка, что в labtarget.mjs браузерных лаб."""
    if os.environ.get("CHROME_PATH"):
        return True
    base = Path.home() / ".cache/puppeteer/chrome-headless-shell"
    return base.exists() and any(base.iterdir())


def registry() -> list[tuple[str, str]]:
    """(id лабы, каталог) из labs.yaml — реестр знает, сколько лаб всего."""
    data = yaml.safe_load(LABS_YAML.read_text(encoding="utf-8"))
    return [(lab["id"], Path(lab["path"]).name) for lab in data["labs"]]


def main(argv: list[str]) -> int:
    labs = registry()
    # Зовут лабу и по id из реестра (`lab-idor`), и по каталогу (`idor`),
    # как в `run_labs.py`.
    lookup: dict[str, tuple[str, str]] = {}
    for lid, d in labs:
        lookup[lid] = lookup[d] = (lid, d)
    unknown = [n for n in argv if n not in lookup]
    if unknown:
        print(f"неизвестная лаба: {unknown}")
        return 2
    picked = [lookup[n] for n in argv] if argv else labs

    node = shutil.which("node")
    chrome = chrome_available()
    results: list[tuple[str, str, str]] = []
    for lab_id, name in picked:
        if name in FIX_PY:
            status, detail = (fix_py(name) if PY.exists()
                              else (SKIPPED, "нет .venv-tools — `make setup`"))
        elif name in FIX_JS:
            if not node:
                status, detail = SKIPPED, "нет node — `make setup`"
            elif not chrome:
                status, detail = SKIPPED, ("нет chrome-headless-shell — "
                                           "`make setup`")
            else:
                status, detail = fix_js(name, FIX_JS[name])
        elif name in CHECK_PY:
            status, detail = check_py(name)
        elif name in SPECIAL:
            status, detail = SPECIAL[name]()
        else:
            status, detail = SKIPPED, ("прогонщик журнала этот вид лабы не "
                                       "знает — поправить tools/lab_journal.py")
        results.append((lab_id, status, detail))
        print(f"{status:<12} {lab_id:<36} {detail}")

    # Стенды обязаны гаснуть за собой: слушающий порт после прогона — это
    # бомба для следующего прогона и для читателя, повторяющего лабу руками.
    busy = []
    for port in PORTS:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                busy.append(port)
        except OSError:
            pass
    if busy:
        print(f"\nпосле прогона слушают порты: {busy} — стенд не погашен, "
              "останови его stand.sh stop")

    closed = [lid for lid, st, _d in results if st == CLOSED]
    skipped = [lid for lid, st, _d in results if st == SKIPPED]
    today = dt.date.today().isoformat()
    print(f"\n{today}: закрыто {len(closed)} из {len(results)}"
          + (f", не проверено {len(skipped)}" if skipped else ""))
    if closed:
        print("строки для журнала («сам / с подсказкой / с решением» и минуты "
              "дописываются руками — research/10 § 5.3):")
        for lid in closed:
            print(f"  {today}  {lid}  закрыта")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
