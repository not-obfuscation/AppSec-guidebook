#!/usr/bin/env python3
"""Схемы mermaid из тем — в SVG, один раз на содержимое.

Часть 7.2 требует схему в виде текста, который лежит в теме рядом с прозой, а не
картинкой в бинарнике. Отсюда два следствия. Первое: в исходнике темы схема
остаётся ограждённым блоком `mermaid` и правится как текст. Второе: на сайте она
должна быть картинкой, а не блоком кода, — и картинку кто-то должен нарисовать.

Рисует `mermaid-cli` (`tools/node/`), в SVG. Почему заранее, а не в браузере
читателя: клиентский mermaid — это загрузка скрипта, а сайт открывается с диска и
в сеть не ходит (`SCOPE.md` § 6). Нарисованный SVG самодостаточен: внутри только
геометрия и текст, внешних ссылок нет, шрифт системный.

Кэш — по содержимому: имя файла считается из самой схемы и параметров
отрисовки, поэтому неизменившаяся схема второй раз не рисуется. Меняются
параметры — меняются все имена, и это правильно: старые картинки нарисованы
другими параметрами.

Отдельно вызывается так:

    .venv-tools/bin/python tools/render_diagrams.py          # все схемы корпуса
    .venv-tools/bin/python tools/render_diagrams.py --list   # только перечислить
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mdtext  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MMDC = ROOT / "tools" / "node" / "node_modules" / ".bin" / "mmdc"
OUT = ROOT / "build" / "diagrams"

# Параметры отрисовки входят в имя файла: белый фон, потому что текст схемы
# тёмный и на тёмной теме сайта он на прозрачном фоне исчезает; ширина задана,
# чтобы схема не рисовалась по ширине окна безголового браузера.
BACKGROUND = "white"
WIDTH = "1000"
PUPPETEER_ARGS = ["--no-sandbox", "--disable-gpu"]
VERSION = "1"          # менять при смене набора параметров

FENCE_RE = mdtext.FENCE_RE


class Unavailable(RuntimeError):
    """mermaid-cli не поставлен: рисовать нечем."""


def digest(source: str) -> str:
    """Имя картинки — от содержимого схемы и параметров отрисовки."""
    key = "\n".join([VERSION, BACKGROUND, WIDTH, source.strip()])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def available() -> bool:
    return MMDC.exists()


def puppeteer_config(out_dir: Path) -> Path:
    """Конфиг браузера. `--no-sandbox` — потому что chrome-headless-shell
    поставлен в домашний каталог и запускается без прав на песочницу."""
    path = out_dir / "puppeteer.json"
    want = json.dumps({"args": PUPPETEER_ARGS}, ensure_ascii=False)
    if not path.exists() or path.read_text(encoding="utf-8") != want:
        path.write_text(want, encoding="utf-8")
    return path


def render(source: str, out_dir: Path = OUT) -> Path:
    """Схема → путь к SVG. Уже нарисованную не рисует заново."""
    if not available():
        raise Unavailable(f"нет {MMDC.relative_to(ROOT)}: `make setup`")
    out_dir.mkdir(parents=True, exist_ok=True)
    svg = out_dir / f"{digest(source)}.svg"
    if svg.exists() and svg.stat().st_size > 0:
        return svg

    src = out_dir / f"{svg.stem}.mmd"
    src.write_text(source.strip() + "\n", encoding="utf-8")
    env = dict(os.environ)
    env.setdefault("PUPPETEER_CACHE_DIR", str(Path.home() / ".cache" / "puppeteer"))
    proc = subprocess.run(
        [str(MMDC), "--input", str(src), "--output", str(svg),
         "--backgroundColor", BACKGROUND, "--width", WIDTH,
         "--puppeteerConfigFile", str(puppeteer_config(out_dir))],
        capture_output=True, text=True, env=env, cwd=str(ROOT))
    if proc.returncode != 0 or not svg.exists():
        raise Unavailable(
            f"mermaid-cli не нарисовал схему: {(proc.stderr or proc.stdout).strip()[:400]}")
    # Ширина «100%» с сохранённым viewBox: схема вписывается в колонку темы и не
    # обрезается на узком экране.
    text = svg.read_text(encoding="utf-8")
    text = re.sub(r'(<svg\b[^>]*?)\swidth="[\d.]+(?:px)?"', r"\1", text, count=1)
    if 'width="100%"' not in text.split(">", 1)[0]:
        text = text.replace("<svg ", '<svg width="100%" ', 1)
    svg.write_text(text, encoding="utf-8")
    src.unlink(missing_ok=True)
    return svg


def diagrams_in(path: Path) -> list[str]:
    """Источники всех схем темы, в порядке появления."""
    raw = mdtext.load(path).raw
    return [m.group("body") for m in FENCE_RE.finditer(raw)
            if m.group("info").strip().lower() == "mermaid"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true",
                    help="перечислить схемы и их имена, не рисовать")
    ap.add_argument("--out", default=str(OUT), help="каталог для SVG")
    args = ap.parse_args()

    out_dir = Path(args.out)
    total = drawn = cached = 0
    failed: list[str] = []
    for path in mdtext.topics():
        for i, source in enumerate(diagrams_in(path), 1):
            total += 1
            name = f"{digest(source)}.svg"
            if args.list:
                print(f"{path.relative_to(ROOT) if path.is_absolute() else path}"
                      f" схема {i} → {name}")
                continue
            existed = (out_dir / name).exists()
            try:
                render(source, out_dir)
            except Unavailable as exc:
                failed.append(f"{path}: {exc}")
                continue
            cached += existed
            drawn += not existed

    if args.list:
        print(f"схем в корпусе: {total}", file=sys.stderr)
        return 0
    print(f"схемы: {total} всего, {drawn} нарисовано, {cached} из кэша"
          + (f", {len(failed)} не удалось" if failed else ""), file=sys.stderr)
    for line in failed:
        print("  " + line, file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
