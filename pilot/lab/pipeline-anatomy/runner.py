#!/usr/bin/env python3
"""Исполнитель конвейера на 90 строк. Ни GitHub Actions, ни GitLab CI.

Воспроизводит четыре свойства настоящего конвейера, и только их:

  1. каждый job начинается с чистого рабочего каталога — исходники есть,
     результатов предыдущего job нет;
  2. состояние между job едет только объявленным артефактом;
  3. кэш восстанавливается, если каталог кэша уже есть, и молча не
     восстанавливается, если его нет; на вердикт кэш не влияет никогда;
  4. вердикт job — код возврата его последней команды.

Ни сети, ни контейнеров: job запускается подпроцессом во временном каталоге.

    python3 runner.py pipeline.yml
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).parent


def parse(path):
    """Читает описание конвейера. Разбор свой: pyyaml в лабе не требуется."""
    stages, jobs, cur, key = [], [], None, None
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split(" #")[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("stages:"):
            stages = [s.strip() for s in line.split(":", 1)[1].strip(" []").split(",")]
        elif line.startswith("- name:"):
            cur = {"name": line.split(":", 1)[1].strip(), "run": [],
                   "artifacts": [], "uses": [], "cache": ""}
            jobs.append(cur)
            key = None
        elif cur is not None and line.startswith("  ") and ":" in line and not line.startswith("    -"):
            key, val = line.strip().split(":", 1)
            val = val.strip()
            if key in ("artifacts", "uses"):
                cur[key] = [v.strip() for v in val.strip("[]").split(",") if v.strip()]
            elif key == "run":
                cur["run"] = []
            else:
                cur[key] = val
        elif cur is not None and line.startswith("    -") and key == "run":
            cur["run"].append(line.strip()[1:].strip())
    return stages, jobs


def run_job(job, artifacts, cache_root):
    ws = tempfile.mkdtemp(prefix="job-")
    shutil.copytree(HERE / "src", pathlib.Path(ws) / "src")
    got = []
    for art in job["uses"]:
        src = artifacts.get(art)
        if src and os.path.exists(src):
            dst = pathlib.Path(ws) / art
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
            got.append(art)
    env = dict(os.environ)
    if job["cache"]:
        cdir = pathlib.Path(cache_root) / job["cache"]
        env["CACHE"] = str(cdir)
        env["CACHE_HIT"] = "1" if cdir.exists() else "0"
        cdir.mkdir(parents=True, exist_ok=True)
    rc, out = 0, []
    for cmd in job["run"]:
        p = subprocess.run(["bash", "-c", cmd], cwd=ws, env=env,
                           capture_output=True, text=True)
        out += (p.stdout + p.stderr).strip().splitlines()
        if p.returncode != 0:
            rc = p.returncode
            break
    saved = []
    for art in job["artifacts"]:
        f = pathlib.Path(ws) / art
        if f.exists():
            keep = pathlib.Path(cache_root).parent / "artifacts" / job["name"]
            keep.mkdir(parents=True, exist_ok=True)
            shutil.copy(f, keep / f.name)
            artifacts[art] = str(keep / f.name)
            saved.append(art)
    shutil.rmtree(ws, ignore_errors=True)
    return rc, got, saved, out


def main(path="pipeline.yml"):
    stages, jobs = parse(path)
    root = tempfile.mkdtemp(prefix="pipe-")
    cache_root = os.path.join(root, "cache")
    artifacts, failed, rows = {}, False, []
    for stage in stages:
        for job in [j for j in jobs if j.get("stage") == stage]:
            if failed:
                rows.append((job["name"], stage, "—", [], [], ["пропущен"]))
                continue
            rc, got, saved, out = run_job(job, artifacts, cache_root)
            rows.append((job["name"], stage, str(rc), got, saved, out))
            if rc != 0:
                failed = True
    w = max(len(r[0]) for r in rows)
    print("%s  стадия     rc  получил -> сохранил" % "job".ljust(w))
    for name, stage, rc, got, saved, out in rows:
        print("%s  %s %s  %s -> %s"
              % (name.ljust(w), stage.ljust(9), rc.rjust(2),
                 ",".join(got) or "—", ",".join(saved) or "—"))
        for line in out[-2:]:
            print("%s    %s" % (" " * w, line))
    print("\nвердикт конвейера: %s" % ("красный" if failed else "зелёный"))
    (HERE / "run.json").write_text(json.dumps(
        [{"job": r[0], "rc": r[1 + 1], "got": r[3], "saved": r[4], "out": r[5]}
         for r in rows], ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "pipeline.yml"))
