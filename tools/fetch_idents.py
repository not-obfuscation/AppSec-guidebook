#!/usr/bin/env python3
"""Загрузка эталонов идентификаторов в локальный кэш для `verify_idents.py`.

    python tools/fetch_idents.py                 # в кэш по умолчанию
    python tools/fetch_idents.py /tmp/idents     # в указанный каталог
    APPSEC_IDENT_CACHE=/tmp/idents python tools/fetch_idents.py

Каталог кэша: аргумент командной строки, переменная `APPSEC_IDENT_CACHE`,
по умолчанию `~/.cache/appsec-idents`. Это единственный скрипт пары, который
ходит в сеть; проверка `verify_idents.py` сеть не трогает и без кэша честно
печатает ПРОПУЩЕНО.

Источники (официальные каталоги):
* CWE    — полный каталог XML с https://cwe.mitre.org/data/downloads.html
           (`cwec_latest.xml.zip`); берутся Weakness, Category и View,
           чтобы отличать «нет такого номера» от «это представление».
* ASVS   — главы требований `5.0/en/0x1*-V*.md` тега `v5.0.0` репозитория
           OWASP/ASVS; список глав спрашивается у GitHub API, сами файлы —
           через raw.githubusercontent.com (codeload на этот тег отвечает
           404).
* WSTG   — тарбол тега `v4.2` репозитория OWASP/wstg; идентификатор —
           из таблицы `|WSTG-XXX-NN|` в шапке каждого теста, название —
           из заголовка первого уровня того же файла.
* Top 10 — индексные страницы https://owasp.org/Top10/2021/ и
           https://owasp.org/Top10/2025/ (категории A01..A10 каждого
           издания).

На выходе в кэше четыре TSV (`cwe.tsv`, `asvs-5.0.0.tsv`, `wstg-4.2.tsv`,
`owasp-top10.tsv`: идентификатор, название, тип) и `PROVENANCE.txt` с адресами
и датой загрузки.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

CWE_URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"
ASVS_API = "https://api.github.com/repos/OWASP/ASVS/contents/5.0/en?ref=v5.0.0"
ASVS_RAW = "https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/"
ASVS_CHAPTER_RE = re.compile(r"^0x\d+-V\d+.*\.md$")
ASVS_REQ_RE = re.compile(r"^\|\s*\*\*(\d+\.\d+\.\d+)\*\*\s*\|\s*(.*?)\s*\|",
                         re.M)
WSTG_URL = "https://codeload.github.com/OWASP/wstg/tar.gz/refs/tags/v4.2"
WSTG_ID_RE = re.compile(r"^\|\s*(WSTG-[A-Z]{4,5}-\d{2})\s*\|", re.M)
WSTG_TITLE_RE = re.compile(r"^#\s+(.+)$", re.M)
TOP10_URLS = {
    "2021": "https://owasp.org/Top10/2021/",
    "2025": "https://owasp.org/Top10/2025/",
}
TOP10_2025_RE = re.compile(r"A(\d{2}):2025\s*[-–—]\s*([^<\n]+)")
TOP10_2021_RE = re.compile(r"A(\d{2})_2021[-_]([^\"/#]+)/")

# Адреса тарболов могут быть недоступны с первой попытки (сброс соединения),
# поэтому скачивание повторяется.
ATTEMPTS = 5


def cache_dir(argv: list[str]) -> Path:
    if argv:
        return Path(argv[0]).expanduser()
    return Path(os.environ.get("APPSEC_IDENT_CACHE",
                               "~/.cache/appsec-idents")).expanduser()


def fetch(url: str) -> bytes:
    """Скачать адрес с повторами; после исчерпания попыток — упасть вслух."""
    last: Exception | None = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "appsec-guidebook fetch_idents"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 — повторяем любой сбой сети
            last = exc
            print(f"  попытка {attempt}/{ATTEMPTS}: {exc}", file=sys.stderr)
    raise SystemExit(f"не удалось скачать {url}: {last}")


def fetch_cwe() -> dict[str, tuple[str, str]]:
    """CWE-номер → (название, вид: weakness/category/view) из полного XML."""
    print(f"CWE: {CWE_URL}")
    with zipfile.ZipFile(io.BytesIO(fetch(CWE_URL))) as zf:
        xml = zf.read(zf.namelist()[0])
    out = {}
    for event, elem in ElementTree.iterparse(io.BytesIO(xml)):
        kind = elem.tag.rsplit("}", 1)[-1]
        if kind in ("Weakness", "Category", "View"):
            out[f"CWE-{elem.get('ID')}"] = (elem.get("Name", ""),
                                            kind.lower())
        elem.clear()
    if len(out) < 1000:
        raise SystemExit(f"подозрительно мало записей CWE: {len(out)}")
    return out


def fetch_asvs() -> dict[str, tuple[str, str]]:
    """v5.0-X.Y.Z → (текст требования, 'requirement') из глав тега v5.0.0."""
    print(f"ASVS: {ASVS_API}")
    listing = json.loads(fetch(ASVS_API))
    chapters = sorted(item["name"] for item in listing
                      if ASVS_CHAPTER_RE.match(item["name"]))
    if len(chapters) < 15:
        raise SystemExit(f"подозрительно мало глав ASVS: {chapters}")
    out = {}
    for name in chapters:
        text = fetch(ASVS_RAW + name).decode("utf-8")
        for ident, req in ASVS_REQ_RE.findall(text):
            out[f"v5.0-{ident}"] = (re.sub(r"\s+", " ", req), "requirement")
    if len(out) < 300:
        raise SystemExit(f"подозрительно мало требований ASVS: {len(out)}")
    return out


def fetch_wstg() -> dict[str, tuple[str, str]]:
    """WSTG-v42-XXX-NN → (название теста, 'test') из тарбола тега v4.2."""
    import tarfile

    print(f"WSTG: {WSTG_URL}")
    blob = fetch(WSTG_URL)
    out = {}
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        for member in tf.getmembers():
            if not (member.isfile() and member.name.endswith(".md")
                    and "/document/" in member.name):
                continue
            text = tf.extractfile(member).read().decode("utf-8")
            ident = WSTG_ID_RE.search(text)
            if not ident:
                continue
            title = WSTG_TITLE_RE.search(text)
            key = ident.group(1).replace("WSTG-", "WSTG-v42-")
            out[key] = (title.group(1).strip() if title else "", "test")
    if len(out) < 90:
        raise SystemExit(f"подозрительно мало тестов WSTG: {len(out)}")
    return out


def fetch_top10() -> dict[str, tuple[str, str]]:
    """ANN:YYYY → (название категории, 'category') с owasp.org."""
    out = {}
    for year, url in TOP10_URLS.items():
        print(f"Top10 {year}: {url}")
        html = fetch(url).decode("utf-8", errors="replace")
        if year == "2025":
            pairs = TOP10_2025_RE.findall(html)
        else:
            pairs = [(num, urllib.parse.unquote(name).replace("_", " "))
                     for num, name in TOP10_2021_RE.findall(html)]
        for num, name in pairs:
            if 1 <= int(num) <= 10:
                out[f"A{num}:{year}"] = (name.strip(), "category")
        got = sorted(k for k in out if k.endswith(year))
        if len(got) != 10:
            raise SystemExit(f"ожидалось 10 категорий Top 10 {year}, "
                             f"получено {len(got)}: {got}")
    return out


def write_tsv(path: Path, data: dict[str, tuple[str, str]]) -> None:
    lines = [f"{ident}\t{name}\t{kind}"
             for ident, (name, kind) in sorted(data.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  {path.name}: {len(data)} записей")


def main(argv: list[str]) -> int:
    dest = cache_dir(argv)
    dest.mkdir(parents=True, exist_ok=True)
    write_tsv(dest / "cwe.tsv", fetch_cwe())
    write_tsv(dest / "asvs-5.0.0.tsv", fetch_asvs())
    write_tsv(dest / "wstg-4.2.tsv", fetch_wstg())
    write_tsv(dest / "owasp-top10.tsv", fetch_top10())
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (dest / "PROVENANCE.txt").write_text(
        f"загружено {stamp} скриптом tools/fetch_idents.py\n"
        f"CWE:    {CWE_URL}\n"
        f"ASVS:   {ASVS_API} (+ {ASVS_RAW}<глава>)\n"
        f"WSTG:   {WSTG_URL}\n"
        f"Top10:  {', '.join(TOP10_URLS.values())}\n", encoding="utf-8")
    print(f"кэш готов: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
