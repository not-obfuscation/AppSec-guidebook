#!/usr/bin/env python3
"""Прогон всех лаб и сверка semgrep-правил — цель `make labs`.

    .venv-tools/bin/python tools/run_labs.py                # всё, по кругу
    .venv-tools/bin/python tools/run_labs.py idor zap-scanning  # выборочно

Критерии по видам лаб:

  «почини» (code.py + solution.py + tests.py + hack.py)
      tests.py — код 0 и на уязвимом, и на исправленном файле;
      hack.py  — код 1 на уязвимом (эксплойт работает), 0 на исправленном.
      Цель выбирается переменной LAB_TARGET, интерпретатор — .venv-tools:
      jwt-basics, jwt-attacks и crypto-misuse тянут PyJWT и cryptography.

  браузерные (same-origin-policy, xss-*, csrf-mechanics)
      то же самое для tests.mjs и hack.mjs под node; браузер — тот же
      chrome-headless-shell, которым гайдбук рисует схемы.

  нестандартные (собственные check.py/check.sh)
      эталон решения применяется во временной копии каталога лабы, и
      собственная проверялка обязана ответить «зачтено» (код 0). Рабочие
      файлы лаб в репозитории хранятся в исходном, не починенном виде, и
      прогон их не трогает: вся подмена — только в копии.

Серверные лабы (zap-scanning, developer-communication) поднимают стенд на
127.0.0.1:8081/8082; стенд останавливается в finally, а в конце прогона порты
проверяются: слушающий процесс после прогона — провал самого прогонщика.

Прогон последовательный и без сети: браузерные лабы режут разрешение имён
флагом, реестр supply-chain-threats — файловый, стенды слушают только петлю.

Код возврата: 0 — всё сошлось, 1 — есть расхождения, 2 — неизвестные имена.
"""

import csv
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import LABS_YAML, ROOT

PY = ROOT / ".venv-tools/bin/python"
SEMGREP = ROOT / ".venv-tools/bin/semgrep"
LABS = ROOT / "pilot/lab"

# Лабы «почини» на Python: четыре прогона на каждую (см. докстринг модуля).
FIX_PY = [
    "business-logic-flaws", "crypto-misuse", "docker-insecure-practices",
    "fail-open", "idor",
    "jwt-attacks", "jwt-basics", "linux-capabilities",
    "linux-file-permissions", "linux-setuid", "oauth-basics",
    "os-command-injection", "parameterized-queries", "password-storage",
    "path-traversal", "privilege-escalation-vertical", "race-conditions",
    "sqli-basics", "ssrf-basics",
]

# Браузерные лабы: каталог → расширение целевого файла.
FIX_JS = {
    "same-origin-policy": "js",
    "xss-dom": "js",
    "xss-reflected": "mjs",
    "xss-contexts": "mjs",
    "csrf-mechanics": "mjs",
}

# Нестандартные лабы со своими проверялками: ключ — каталог, значение —
# функция ниже. Унифицировать их не надо: у каждой свой эталон и свой ритуал.
SPECIAL = [
    "cve-cvss", "sast-principles", "zap-scanning", "supply-chain-threats",
    "pipeline-anatomy", "pipeline-security", "quality-gates",
    "developer-communication", "semgrep-rules",
]

# Порты, которые лабы поднимают на петле. После прогона все обязаны быть
# свободны: оставшийся процесс — это бомба замедленного действия для следующего
# прогона и для читателя, повторяющего лабу руками.
PORTS = [8081, 8082, 8083, 8121, 8122, 8123, 8124, 8125, 8126]

FAILURES: list[str] = []


def expect(what: str, argv: list, cwd: Path, code: int,
           env: dict | None = None, timeout: int = 300) -> None:
    """Один прогон с ожидаемым кодом возврата; расхождение — в журнал."""
    try:
        proc = subprocess.run([str(a) for a in argv], cwd=cwd, env=env,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        FAILURES.append(f"{what}: превышен таймаут {timeout} с")
        print(f"ПАДАЕТ  {what}: таймаут {timeout} с")
        return
    if proc.returncode != code:
        FAILURES.append(f"{what}: ждали код {code}, получили {proc.returncode}")
        print(f"ПАДАЕТ  {what}: ждали код {code}, получили {proc.returncode}")
        for line in (proc.stdout + proc.stderr).splitlines()[-15:]:
            print(f"        {line}")


def temp_lab(name: str) -> tuple[tempfile.TemporaryDirectory, Path]:
    """Временная копия каталога лабы: эталон применяется в ней, а не в репозитории."""
    tmp = tempfile.TemporaryDirectory(prefix=f"lab-{name}-")
    lab = Path(tmp.name) / name
    shutil.copytree(LABS / name, lab, symlinks=True)
    return tmp, lab


def stand(lab: Path, cmd: str) -> None:
    """Команда стенду лабы: start/stop/reset через её собственный stand.sh.

    Путь абсолютный не случайно: stand.sh перевызывает себя через `$0`, и
    относительное имя после `cd` внутри скрипта уже не находится.
    """
    subprocess.run(["sh", str(lab / "stand.sh"), cmd], cwd=lab,
                   capture_output=True, text=True, timeout=60)


# --- «почини» ---------------------------------------------------------------

def fix_py(name: str) -> None:
    lab = LABS / name
    for script, target, code in (("tests.py", "code.py", 0),
                                 ("tests.py", "solution.py", 0),
                                 ("hack.py", "code.py", 1),
                                 ("hack.py", "solution.py", 0)):
        env = os.environ | {"LAB_TARGET": target}
        expect(f"{name}: {script} на {target}", [PY, script], lab, code, env=env)


def fix_js(name: str, ext: str) -> None:
    lab = LABS / name
    for script, target, code in (("tests.mjs", f"code.{ext}", 0),
                                 ("tests.mjs", f"solution.{ext}", 0),
                                 ("hack.mjs", f"code.{ext}", 1),
                                 ("hack.mjs", f"solution.{ext}", 0)):
        env = os.environ | {"LAB_TARGET": target}
        expect(f"{name}: {script} на {target}", ["node", script], lab, code,
               env=env, timeout=600)


# --- задачи чтения: бланк ответов заполняется по разметке -------------------

def fill_answers(lab: Path, match: tuple[str, ...]) -> None:
    """Заполнить answers.csv из key.yaml: вердикт и признак из разметки.

    Проверялка сверяет вердикт с ключом и требует непустой признак, а порядок
    строк в бланке совпадает с порядком ключа — этим и пользуемся.
    """
    key = yaml.safe_load((lab / "key.yaml").read_text(encoding="utf-8"))["key"]
    lines = [ln for ln in (lab / "answers.csv").read_text(encoding="utf-8").splitlines()
             if not ln.lstrip().startswith("#")]
    rows = list(csv.DictReader(lines))
    for row in rows:
        item = next((k for k in key
                     if all(str(k[f]) == row[f] for f in match)), None)
        if item is None:
            raise ValueError(f"строка бланка без пары в ключе: {row}")
        row["вердикт"] = item["вердикт"]
        row["признак"] = item.get("признак") or item["почему"]
    with open(lab / "answers.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def lab_cve_cvss() -> None:
    # Эталон ответов лежит рядом готовым файлом — бланк просто заменяется.
    tmp, lab = temp_lab("cve-cvss")
    try:
        shutil.copy(lab / "solution.csv", lab / "answers.csv")
        expect("cve-cvss: check.py", [PY, "check.py"], lab, 0)
    finally:
        tmp.cleanup()


def lab_sast_principles() -> None:
    tmp, lab = temp_lab("sast-principles")
    try:
        fill_answers(lab, match=("инструмент", "файл", "строка", "правило"))
        expect("sast-principles: check.py", [PY, "check.py"], lab, 0)
    finally:
        tmp.cleanup()


def lab_zap_scanning() -> None:
    tmp, lab = temp_lab("zap-scanning")
    try:
        # Задача чтения: бланк, заполненный по разметке, обязан быть зачтён.
        # Сканера для этого не нужно: сверка идёт по сохранённым прогонам runs/.
        fill_answers(lab, match=("строка", "правило"))
        expect("zap-scanning: check.py", [PY, "check.py"], lab, 0)
        # Уязвимый стенд: лавка работает, эксплойт проходит.
        stand(lab, "reset")
        expect("zap-scanning: tests.py на уязвимом", [PY, "tests.py"], lab, 0)
        expect("zap-scanning: hack.py на уязвимом", [PY, "hack.py"], lab, 1)
        # Эталон починки: hack.py и tests.py зелёные разом.
        shutil.copy(lab / "solution/app.py", lab / "stand/app.py")
        stand(lab, "reset")
        expect("zap-scanning: check_fix.py на эталоне",
               [PY, "check_fix.py"], lab, 0)
    finally:
        stand(lab, "stop")
        tmp.cleanup()


# --- «почини» со своими проверялками -----------------------------------------

def lab_supply_chain() -> None:
    # Эталон фикса — fix.sh.example; реестр пакетов файловый, сеть не нужна.
    tmp, lab = temp_lab("supply-chain-threats")
    try:
        shutil.copy(lab / "fix.sh.example", lab / "fix.sh")
        expect("supply-chain-threats: check.py", [PY, "check.py"], lab, 0)
    finally:
        tmp.cleanup()


def lab_pipeline_anatomy() -> None:
    tmp, lab = temp_lab("pipeline-anatomy")
    try:
        shutil.copy(lab / "solution-pipeline.yml", lab / "pipeline.yml")
        expect("pipeline-anatomy: check.py", [PY, "check.py"], lab, 0)
    finally:
        tmp.cleanup()


def lab_pipeline_security() -> None:
    # Эталоны — оба *.example: исправленные описания конвейеров.
    tmp, lab = temp_lab("pipeline-security")
    try:
        shutil.copy(lab / ".github/workflows/pr-greeter.yml.example",
                    lab / ".github/workflows/pr-greeter.yml")
        shutil.copy(lab / ".gitlab-ci.yml.example", lab / ".gitlab-ci.yml")
        expect("pipeline-security: check.py", [PY, "check.py"], lab, 0)
    finally:
        tmp.cleanup()


def lab_quality_gates() -> None:
    # Эталон гейта — gate.py.example (рабочий gate.py — заготовка-ноль).
    tmp, lab = temp_lab("quality-gates")
    try:
        shutil.copy(lab / "gate.py.example", lab / "gate.py")
        expect("quality-gates: check.py", [PY, "check.py"], lab, 0)
    finally:
        tmp.cleanup()


def lab_developer_communication() -> None:
    # Эталонные заявки кладутся поверх бланков, стенд — на 127.0.0.1:8082.
    tmp, lab = temp_lab("developer-communication")
    try:
        for ticket in sorted((lab / "solution").glob("t*.md")):
            shutil.copy(ticket, lab / "tickets" / ticket.name)
        stand(lab, "start")
        expect("developer-communication: check.py", [PY, "check.py"], lab, 0)
    finally:
        stand(lab, "stop")
        tmp.cleanup()


def lab_semgrep_rules() -> None:
    # У лабы есть готовые правила в solution/ с той же разметкой ожиданий:
    # `semgrep --test` обязан сойтись на них. Каталог не копируется —
    # проверялка ничего не пишет.
    expect("semgrep-rules: semgrep --test solution/",
           [SEMGREP, "--test", "--metrics=off", "solution/"],
           LABS / "semgrep-rules", 0)


SPECIAL_FUNCS = {
    "cve-cvss": lab_cve_cvss,
    "sast-principles": lab_sast_principles,
    "zap-scanning": lab_zap_scanning,
    "supply-chain-threats": lab_supply_chain,
    "pipeline-anatomy": lab_pipeline_anatomy,
    "pipeline-security": lab_pipeline_security,
    "quality-gates": lab_quality_gates,
    "developer-communication": lab_developer_communication,
    "semgrep-rules": lab_semgrep_rules,
}


# --- прогон ------------------------------------------------------------------

def check_registry() -> None:
    """Реестр labs.yaml и списки выше обязаны покрывать одни и те же лабы."""
    covered = set(FIX_PY) | set(FIX_JS) | set(SPECIAL)
    registered = {Path(item["path"]).name
                  for item in yaml.safe_load(
                      LABS_YAML.read_text(encoding="utf-8"))["labs"]}
    if covered != registered:
        FAILURES.append(
            f"реестр и прогонщик разошлись: "
            f"лишние в прогонщике {sorted(covered - registered)}, "
            f"не покрыты {sorted(registered - covered)}")


def check_ports() -> None:
    """После прогона на петле не должно слушать ничего из портов лаб."""
    busy = []
    for port in PORTS:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                busy.append(port)
        except OSError:
            pass
    if busy:
        FAILURES.append(f"после прогона слушают порты: {busy}")


def main(argv: list[str]) -> int:
    names = argv or sorted(set(FIX_PY) | set(FIX_JS) | set(SPECIAL))
    unknown = [n for n in names
               if n not in FIX_PY and n not in FIX_JS and n not in SPECIAL_FUNCS]
    if unknown:
        print(f"неизвестная лаба: {unknown}")
        return 2

    check_registry()

    if not argv:
        print("== сверка semgrep-правил (pilot/semgrep/check.py)")
        expect("semgrep-правила: сверка с разметкой",
               [PY, "pilot/semgrep/check.py"], ROOT, 0, timeout=900)

    for name in names:
        print(f"== {name}")
        if name in FIX_PY:
            fix_py(name)
        elif name in FIX_JS:
            fix_js(name, FIX_JS[name])
        else:
            SPECIAL_FUNCS[name]()

    check_ports()

    total = len(names) + (0 if argv else 1)
    if FAILURES:
        print(f"\nИТОГ: провалов {len(FAILURES)} из {total} прогонов:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print(f"\nИТОГ: {total} прогонов, все зелёные; порты свободны")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
