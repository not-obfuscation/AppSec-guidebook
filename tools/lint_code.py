#!/usr/bin/env python3
"""Проверка `C-CODE-SYNTAX`: листинг кода обязан компилироваться целиком.

Читатель копирует листинг и запускает его. Срез, который сам по себе не
компилируется, этому мешает, но и разбор без срезов не пишется — поэтому
договор такой (STYLE.md § 6, `C-CODE-SYNTAX`):

* блок, первая строка которого — комментарий со словом «ФРАГМЕНТ», проверкой
  пропускается: автор честно сказал, что это срез;
* блок без маркера обязан проходить синтаксическую проверку своего языка.

Языки и инструменты:

* `python`     — `compile()`: голый `ast.parse` не ловит `return` вне функции;
* `javascript` — `node --check` временного `.mjs`-файла: модульный режим ловит
                 и `return` на верхнем уровне;
* `bash`       — `bash -n` временного файла;
* `yaml`       — `yaml.safe_load_all`, а блок, похожий на правило semgrep
                 (есть `rules:` и `message:` или `patterns:`), дополнительно
                 гоняется через `semgrep --validate`: читатель копирует правило
                 в свой пайплайн, и невалидное правило — та же ложь, что
                 невалидный код.

Листинги прочих языков (`http`, `text`, `mermaid`, …) проверять нечем — они
пропускаются без маркера. Формат вывода — `путь:строка:столбец:ПРАВИЛО:
сообщение`, как у Vale. Выход 1, если есть ошибка. Содержимое `content/**`
скрипт только читает.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mdtext

ERROR, WARNING = "error", "warning"
RULE = "C-CODE-SYNTAX"

# Слово-договор: первая строка листинга, комментарием на языке блока.
MARKER = "ФРАГМЕНТ"

LANG_PY = {"python", "py"}
LANG_JS = {"javascript", "js"}
LANG_BASH = {"bash", "sh"}
LANG_YAML = {"yaml", "yml"}

NODE = shutil.which("node")
BASH = shutil.which("bash")
# semgrep живёт рядом с интерпретатором проверок (.venv-tools): `make labs`
# зовёт его оттуда же. Запуск скрипта другим python — не повод молча терять
# проверку правил: ищем и в PATH.
SEMGREP = (Path(sys.executable).with_name("semgrep")
           if Path(sys.executable).with_name("semgrep").exists()
           else shutil.which("semgrep"))


class Finding:
    __slots__ = ("path", "line", "col", "rule", "level", "message")

    def __init__(self, path, line, col, rule, level, message):
        self.path, self.line, self.col = str(path), line, col
        self.rule, self.level, self.message = rule, level, message

    def __str__(self):
        return f"{self.path}:{self.line}:{self.col}:{self.rule}:{self.message}"

    def sort_key(self):
        return (self.path, self.line, self.col, self.rule)


def body_lines(f) -> list[str]:
    """Строки листинга без ограждений и без отступа внешнего списка."""
    lines = f.body.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [raw[len(f.indent):] if raw.startswith(f.indent) else raw
            for raw in lines]


def is_fragment(f) -> bool:
    """Договор о маркере: слово «ФРАГМЕНТ» в первой строке кода."""
    lines = body_lines(f)
    return bool(lines) and MARKER in lines[0]


def check_python(path, f, code) -> list[Finding]:
    try:
        # compile, а не ast.parse: `return` вне функции — ошибка именно на
        # компиляции, разбор его пропускает (аудит 2026-08-30).
        compile(code, str(path), "exec")
    except SyntaxError as e:
        return [Finding(path, f.fence_line + (e.lineno or 1), e.offset or 1,
                        RULE, ERROR, f"python не компилируется: {e.msg}")]
    return []


def run_probe(argv: list[str], timeout: float | None = None):
    """Прогон проверяющего инструмента: сбой инструмента — не traceback.

    Пойманный сбой возвращается как строка причины, чтобы стать замечанием
    уровня error: красный вердикт с понятным текстом, а не упавший линтер.
    """
    try:
        return subprocess.run(argv, capture_output=True, text=True,
                              timeout=timeout), ""
    except subprocess.TimeoutExpired:
        return None, f"инструмент не завершился за {timeout:.0f} с"
    except OSError as e:
        return None, f"инструмент не запустился: {e}"


def check_js(path, f, code, tmp) -> list[Finding]:
    # `.mjs`, а не `.js`: в модуле `return` на верхнем уровне запрещён,
    # и `node --check` это видит.
    probe = tmp / "block.mjs"
    probe.write_text(code, encoding="utf-8")
    proc, fail = run_probe(["node", "--check", str(probe)])
    if fail:
        return [Finding(path, f.fence_line + 1, 1, RULE, ERROR, f"javascript: {fail}")]
    if proc.returncode == 0:
        return []
    m = re.search(rf"{re.escape(str(probe))}:(\d+)", proc.stderr)
    line = f.fence_line + (int(m.group(1)) if m else 1)
    msg = next((ln.strip() for ln in proc.stderr.splitlines()
                if "Error" in ln), "синтаксическая ошибка")
    return [Finding(path, line, 1, RULE, ERROR, f"javascript не разбирается: {msg}")]


BASH_LINE_RE = re.compile(r"line (\d+)")


def check_bash(path, f, code, tmp) -> list[Finding]:
    probe = tmp / "block.sh"
    probe.write_text(code, encoding="utf-8")
    proc, fail = run_probe(["bash", "-n", str(probe)])
    if fail:
        return [Finding(path, f.fence_line + 1, 1, RULE, ERROR, f"bash: {fail}")]
    if proc.returncode == 0:
        return []
    m = BASH_LINE_RE.search(proc.stderr)
    line = f.fence_line + (int(m.group(1)) if m else 1)
    msg = proc.stderr.strip().splitlines()[-1]
    msg = msg.split(":", 2)[-1].strip() or "синтаксическая ошибка"
    return [Finding(path, line, 1, RULE, ERROR, f"bash не разбирается: {msg}")]


def looks_like_semgrep(code: str) -> bool:
    return "rules:" in code and ("message:" in code or "patterns:" in code)


def check_yaml(path, f, code, tmp) -> list[Finding]:
    import yaml

    out = []
    try:
        list(yaml.safe_load_all(code))
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        line = f.fence_line + 1 + (mark.line if mark else 0)
        problem = getattr(e, "problem", None) or str(e).splitlines()[0]
        out.append(Finding(path, line, 1, RULE, ERROR,
                           f"yaml не разбирается: {problem}"))
        return out  # битый yaml semgrep'у скармливать бессмысленно
    if looks_like_semgrep(code):
        if SEMGREP is None:
            return [Finding(path, f.fence_line + 1, 1, RULE, WARNING,
                            "похоже на правило semgrep, а самого semgrep нет — "
                            "`make setup` (.venv-tools)")]
        probe = tmp / "block.yaml"
        probe.write_text(code, encoding="utf-8")
        proc, fail = run_probe(
            [str(SEMGREP), "--validate", "--config", str(probe)], timeout=120)
        if fail:
            return [Finding(path, f.fence_line + 1, 1, RULE, ERROR,
                            f"semgrep: {fail}")]
        if proc.returncode != 0:
            text = (proc.stdout + proc.stderr).strip().splitlines()
            tail = text[-1][:120] if text else "код возврата не 0"
            out.append(Finding(path, f.fence_line + 1, 1, RULE, ERROR,
                               f"semgrep --validate не принял правило: {tail}"))
    return out


def check_file(path, tmp) -> list[Finding]:
    doc = mdtext.load(path)
    out = []
    for f in doc.fences:
        lang = f.info.split()[0].lower() if f.info else ""
        if lang not in LANG_PY | LANG_JS | LANG_BASH | LANG_YAML:
            continue
        if is_fragment(f):
            continue
        code = "\n".join(body_lines(f)) + "\n"
        if lang in LANG_PY:
            out += check_python(path, f, code)
        elif lang in LANG_JS:
            out += check_js(path, f, code, tmp)
        elif lang in LANG_BASH:
            out += check_bash(path, f, code, tmp)
        else:
            out += check_yaml(path, f, code, tmp)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--summary", action="store_true",
                    help="печатать сводку по правилам вместо списка замечаний")
    ap.add_argument("--json", action="store_true",
                    help="по одному объекту JSON на замечание, с уровнем: "
                         "этим форматом замечания читает tools/check.py")
    ap.add_argument("paths", nargs="*", help="файлы; по умолчанию content/**/*.md")
    args = ap.parse_args()

    if NODE is None:
        sys.stderr.write("нет node в PATH — javascript проверить нечем, "
                         "`make setup`\n")
        return 2
    if BASH is None:
        sys.stderr.write("нет bash в PATH\n")
        return 2

    paths = [Path(p) for p in args.paths] or mdtext.topics()
    findings: list[Finding] = []
    with tempfile.TemporaryDirectory(prefix="lint-code-") as d:
        tmp = Path(d)
        for path in paths:
            findings += check_file(path, tmp)
    findings.sort(key=Finding.sort_key)

    if args.json:
        for f in findings:
            print(json.dumps({"path": f.path, "line": f.line, "col": f.col,
                              "rule": f.rule, "level": f.level,
                              "message": f.message}, ensure_ascii=False))
    elif args.summary:
        per = defaultdict(int)
        for f in findings:
            per[(f.rule, f.level)] += 1
        for (rule, level), n in sorted(per.items()):
            print(f"{rule:<14} {level:<8} {n}")
    else:
        for f in findings:
            print(f)

    errors = sum(1 for f in findings if f.level == ERROR)
    if not args.json:
        print(f"\nlint_code: {errors} error, {len(findings) - errors} warning "
              f"({len(paths)} файлов)", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
